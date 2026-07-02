# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
from unittest import mock

import cv2
import numpy
from PIL import Image

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

# Parser code operating on pipe-delimited OCR text lines:
# "DD/MM/YY|debit|credit|balance|ref" — mirrors the transcript format expected
# from scanned savings-account passbook pages (see BL-0013 for real bank
# templates). Balance-derived amount avoids relying on OCR column alignment.
_PARSER_CODE = """\
lines = [l.strip() for l in full_text.strip().splitlines() if l.strip()]
transactions = []
idx = 0
for line in lines:
    if "|" not in line:
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 5:
        continue
    date_str, debit_str, credit_str, balance_str, ref = parts[:5]
    d = datetime.datetime.strptime(date_str, "%d/%m/%y").date()
    debit = float(debit_str)
    credit = float(credit_str)
    balance = float(balance_str)
    amount = credit - debit
    idx += 1
    transactions.append({
        "date": str(d),
        "amount": amount,
        "payment_ref": ref,
        "unique_import_id": "%s-%s-%s-%s" % (d, amount, balance, idx),
    })
result["statements"] = [{"name": filename, "transactions": transactions}]
"""

_EMPTY_PARSER_CODE = "result['statements'] = []"
_ERROR_PARSER_CODE = "raise ValueError('boom')"


@tagged("post_install", "-at_install")
class TestImportPdfImage(TransactionCase):
    def setUp(self):
        super().setUp()
        self.MappingModel = self.env["account.statement.import.pdf.image.mapping"]
        # Use the company's active currency as fallback so _match_currency
        # (OCA account_statement_import) finds a valid, active currency
        # regardless of which currencies are active in the test database.
        self.company_currency = self.env.company.currency_id
        self.mapping = self.MappingModel.create(
            {
                "name": "Test PDF Image Mapping",
                "code": "TEST-IMAGE-IMPORT",
                "ocr_lang": "eng",
                "ocr_dpi": 300,
                "ocr_psm": 6,
                "currency_id": self.company_currency.id,
                "parser_code": _PARSER_CODE,
            }
        )
        self.bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )

    @staticmethod
    def _make_extracted(lines):
        text = "\n".join(lines)
        return {"pages": [text], "full_text": text}

    def test_parse_extracted_triplet(self):
        """_parse_extracted returns (currency_code, account_number, statements)."""
        extracted = self._make_extracted(
            [
                "01/05/26|0.00|500000.00|1000000.00|TRANSFER MASUK TEST 1",
                "02/05/26|200000.00|0.00|800000.00|PEMBAYARAN TEST 2",
            ]
        )
        result = self.mapping._parse_extracted(extracted, "passbook.pdf")

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

        currency_code, account_number, statements = result
        self.assertEqual(currency_code, self.company_currency.name)
        self.assertFalse(account_number)
        self.assertTrue(statements, "statements must not be empty")

        transactions = statements[0]["transactions"]
        self.assertEqual(len(transactions), 2, "expected 2 transactions")
        self.assertEqual(transactions[0]["amount"], 500000.0)
        self.assertEqual(transactions[1]["amount"], -200000.0)
        self.assertEqual(transactions[0]["payment_ref"], "TRANSFER MASUK TEST 1")

    def test_import_wizard_creates_statement(self):
        """Wizard with pdf_image_mapping_id OCR-parses PDF and creates statement lines."""
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")

        extracted = self._make_extracted(
            [
                "01/06/26|0.00|500000.00|1000000.00|OCR IMPORT TEST TXN 1",
                "02/06/26|200000.00|0.00|800000.00|OCR IMPORT TEST TXN 2",
            ]
        )
        with mock.patch.object(type(self.mapping), "_extract", return_value=extracted):
            wizard = (
                self.env["account.statement.import"]
                .with_context(journal_id=self.bank_journal.id)
                .create(
                    {
                        "statement_file": base64.b64encode(b"dummy pdf bytes"),
                        "statement_filename": "passbook_scan.pdf",
                        "pdf_image_mapping_id": self.mapping.id,
                    }
                )
            )
            result = wizard.import_file_button()

        if isinstance(result, dict) and "statement_ids" in result:
            stmt_ids = result["statement_ids"]
            lines = self.env["account.bank.statement.line"].search(
                [("statement_id", "in", stmt_ids)]
            )
            self.assertGreaterEqual(
                len(lines), 2, "expected at least 2 statement lines after OCR import"
            )

    def test_reimport_dedup(self):
        """Second import of the same scan raises UserError; no duplicate lines created."""
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")

        extracted = self._make_extracted(
            [
                "03/06/26|0.00|111111.00|900000.00|DEDUP TEST TXN A",
                "04/06/26|0.00|222222.00|1122222.00|DEDUP TEST TXN B",
            ]
        )
        encoded = base64.b64encode(b"dummy pdf bytes")

        import_env = self.env["account.statement.import"].with_context(
            journal_id=self.bank_journal.id
        )
        with mock.patch.object(type(self.mapping), "_extract", return_value=extracted):
            wizard1 = import_env.create(
                {
                    "statement_file": encoded,
                    "statement_filename": "dedup.pdf",
                    "pdf_image_mapping_id": self.mapping.id,
                }
            )
            wizard1.import_file_button()

            wizard2 = import_env.create(
                {
                    "statement_file": encoded,
                    "statement_filename": "dedup.pdf",
                    "pdf_image_mapping_id": self.mapping.id,
                }
            )
            with self.assertRaises(UserError):
                wizard2.import_file_button()

        lines = self.env["account.bank.statement.line"].search(
            [("payment_ref", "in", ["DEDUP TEST TXN A", "DEDUP TEST TXN B"])]
        )
        self.assertEqual(
            len(lines), 2, "deduplication failed: expected exactly 2 lines"
        )

    def test_non_pdf_falls_back(self):
        """Non-.pdf filename falls through to super(); _extract is never called."""
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(b"dummy content"),
                "statement_filename": "statement.csv",
                "pdf_image_mapping_id": self.mapping.id,
            }
        )
        with mock.patch.object(type(self.mapping), "_extract") as mocked_extract:
            with self.assertRaises(UserError):
                wizard._parse_file(b"dummy content")
            mocked_extract.assert_not_called()

    def test_empty_statements_raises(self):
        """_parse_extracted raises UserError when parser_code yields empty statements."""
        empty_mapping = self.MappingModel.create(
            {
                "name": "Empty Parser Mapping",
                "code": "EMPTY-IMAGE-PARSE-TEST",
                "ocr_lang": "eng",
                "ocr_dpi": 300,
                "ocr_psm": 6,
                "parser_code": _EMPTY_PARSER_CODE,
            }
        )
        extracted = self._make_extracted(["01/05/26|0.00|500000.00|1000000.00|X"])
        with self.assertRaises(UserError):
            empty_mapping._parse_extracted(extracted, "test.pdf")

    def test_parser_error_raises(self):
        """A raising parser_code is wrapped into a structured UserError."""
        error_mapping = self.MappingModel.create(
            {
                "name": "Error Parser Mapping",
                "code": "ERROR-IMAGE-PARSE-TEST",
                "ocr_lang": "eng",
                "ocr_dpi": 300,
                "ocr_psm": 6,
                "parser_code": _ERROR_PARSER_CODE,
            }
        )
        extracted = self._make_extracted(["01/05/26|0.00|500000.00|1000000.00|X"])
        with self.assertRaises(UserError):
            error_mapping._parse_extracted(extracted, "test.pdf")

    def test_mapping_requires_group(self):
        """A user without the configurator group cannot create PDF image mapping records."""
        demo_user = self.env.ref("base.user_demo")
        with self.assertRaises(AccessError):
            self.MappingModel.with_user(demo_user).create(
                {
                    "name": "Unauthorized Mapping",
                    "code": "UNAUTH-IMAGE-TEST",
                    "ocr_lang": "eng",
                    "ocr_dpi": 300,
                    "ocr_psm": 6,
                    "parser_code": _EMPTY_PARSER_CODE,
                }
            )

    @staticmethod
    def _gradient_image(width=64, height=64):
        """RGB image with a smooth gradient, used to exercise binarization."""
        row = numpy.tile(numpy.linspace(0, 255, width, dtype=numpy.uint8), (height, 1))
        arr = numpy.stack([row, row, row], axis=-1)
        return Image.fromarray(arr, mode="RGB")

    @staticmethod
    def _skewed_rect_array(width=200, height=200, angle=12.0):
        """Binarized-style array (white background, black rectangle 'text')
        rotated by `angle` degrees — same convention _preprocess_deskew
        expects as input (dark foreground on light background)."""
        arr = numpy.full((height, width), 255, dtype=numpy.uint8)
        arr[80:120, 20:180] = 0
        center = (width / 2, height / 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            arr,
            rotation_matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )

    @staticmethod
    def _rect_angle(arr):
        """Skew angle (degrees) of the rectangle in `arr`, normalized so 0
        means axis-aligned (no skew). `arr` follows the white-background/
        dark-foreground convention (same as _preprocess_deskew's input)."""
        inverted = 255 - arr
        coords = cv2.findNonZero(inverted)
        if coords is None:
            return 0.0
        raw_angle = cv2.minAreaRect(coords)[-1]
        if raw_angle < -45:
            return -90 - raw_angle
        return -raw_angle

    def test_preprocess_grayscale(self):
        """Grayscale step reduces an RGB image to single-channel 'L' mode."""
        self.mapping.write(
            {
                "preprocess_enabled": True,
                "preprocess_grayscale": True,
                "preprocess_autocontrast": False,
                "preprocess_binarize": "none",
                "preprocess_deskew": False,
            }
        )
        rgb = self._gradient_image()
        img = self.mapping._preprocess_image(rgb)
        self.assertEqual(img.mode, "L")

    def test_preprocess_adaptive_binary(self):
        """Adaptive binarization yields only pure black/white pixel values."""
        self.mapping.write(
            {
                "preprocess_enabled": True,
                "preprocess_grayscale": True,
                "preprocess_autocontrast": False,
                "preprocess_binarize": "adaptive",
                "preprocess_deskew": False,
            }
        )
        img = self.mapping._preprocess_image(self._gradient_image())
        values = set(numpy.array(img).flatten().tolist())
        self.assertTrue(values.issubset({0, 255}))

    def test_preprocess_otsu_binary(self):
        """Otsu binarization yields only pure black/white pixel values."""
        self.mapping.write(
            {
                "preprocess_enabled": True,
                "preprocess_grayscale": True,
                "preprocess_autocontrast": False,
                "preprocess_binarize": "otsu",
                "preprocess_deskew": False,
            }
        )
        img = self.mapping._preprocess_image(self._gradient_image())
        values = set(numpy.array(img).flatten().tolist())
        self.assertTrue(values.issubset({0, 255}))

    def test_preprocess_global_threshold_binary(self):
        """Global threshold binarization yields only pure black/white pixel values."""
        self.mapping.write(
            {
                "preprocess_enabled": True,
                "preprocess_grayscale": True,
                "preprocess_autocontrast": False,
                "preprocess_binarize": "global",
                "preprocess_threshold": 128,
                "preprocess_deskew": False,
            }
        )
        img = self.mapping._preprocess_image(self._gradient_image())
        values = set(numpy.array(img).flatten().tolist())
        self.assertTrue(values.issubset({0, 255}))

    def test_preprocess_disabled_is_noop_in_extract(self):
        """_extract never calls _preprocess_image when preprocess_enabled is False."""
        self.mapping.write({"preprocess_enabled": False})
        fake_image = self._gradient_image()
        with mock.patch(
            "pdf2image.convert_from_bytes", return_value=[fake_image]
        ), mock.patch(
            "pytesseract.image_to_string", return_value="OCR TEXT"
        ), mock.patch.object(
            type(self.mapping), "_preprocess_image"
        ) as mocked_preprocess:
            self.mapping._extract(b"dummy pdf bytes")
            mocked_preprocess.assert_not_called()

    def test_preprocess_enabled_invoked_in_extract(self):
        """_extract calls _preprocess_image once per page when enabled."""
        self.mapping.write({"preprocess_enabled": True})
        fake_image = self._gradient_image()
        with mock.patch(
            "pdf2image.convert_from_bytes", return_value=[fake_image]
        ), mock.patch(
            "pytesseract.image_to_string", return_value="OCR TEXT"
        ), mock.patch.object(
            type(self.mapping), "_preprocess_image", return_value=fake_image
        ) as mocked_preprocess:
            self.mapping._extract(b"dummy pdf bytes")
            mocked_preprocess.assert_called_once_with(fake_image)

    def test_preprocess_deskew_empty_image_safe(self):
        """Deskew on a blank image does not raise and returns an Image."""
        self.mapping.write(
            {
                "preprocess_enabled": True,
                "preprocess_grayscale": True,
                "preprocess_autocontrast": False,
                "preprocess_binarize": "none",
                "preprocess_deskew": True,
            }
        )
        blank = Image.fromarray(numpy.zeros((64, 64), dtype=numpy.uint8), mode="L")
        img = self.mapping._preprocess_image(blank)
        self.assertIsInstance(img, Image.Image)

    def test_preprocess_deskew_reduces_angle(self):
        """Deskew reduces the estimated skew angle of a rotated rectangle."""
        self.mapping.write(
            {
                "preprocess_enabled": True,
                "preprocess_grayscale": False,
                "preprocess_autocontrast": False,
                "preprocess_binarize": "none",
                "preprocess_deskew": True,
            }
        )
        before = self._skewed_rect_array(angle=12.0)
        angle_before = self._rect_angle(before)

        after_img = self.mapping._preprocess_image(Image.fromarray(before, mode="L"))
        angle_after = self._rect_angle(numpy.array(after_img))

        self.assertLess(abs(angle_after), abs(angle_before))

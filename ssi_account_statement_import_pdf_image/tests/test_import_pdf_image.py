# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
from unittest import mock

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
result["currency_code"] = "IDR"
result["statements"] = [{"name": filename, "transactions": transactions}]
"""

_EMPTY_PARSER_CODE = "result['statements'] = []"
_ERROR_PARSER_CODE = "raise ValueError('boom')"


@tagged("post_install", "-at_install")
class TestImportPdfImage(TransactionCase):
    def setUp(self):
        super().setUp()
        self.MappingModel = self.env["account.statement.import.pdf.image.mapping"]
        self.mapping = self.MappingModel.create(
            {
                "name": "Test PDF Image Mapping",
                "code": "TEST-IMAGE-IMPORT",
                "ocr_lang": "eng",
                "ocr_dpi": 300,
                "ocr_psm": 6,
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
        self.assertEqual(currency_code, "IDR")
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

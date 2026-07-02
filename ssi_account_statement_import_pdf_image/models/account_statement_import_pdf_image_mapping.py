# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import cv2
import numpy
from PIL import Image

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, wrap_module


class AccountStatementImportPdfImageMapping(models.Model):
    _name = "account.statement.import.pdf.image.mapping"
    _inherit = ["mixin.master_data"]
    _description = "PDF Image Statement Import Mapping"

    ocr_lang = fields.Char(
        string="OCR Language(s)",
        default="eng",
        required=True,
        help=(
            "Tesseract language specification used to OCR each rendered page, "
            "e.g. 'eng' or 'eng+ind' for combined English and Indonesian. "
            "The corresponding Tesseract language pack(s) must be installed "
            "on the Odoo image."
        ),
    )
    ocr_dpi = fields.Integer(
        string="Render DPI",
        default=300,
        required=True,
        help=(
            "Resolution (dots per inch) used to render each PDF page into an "
            "image before running OCR, via pdf2image/poppler. Higher values "
            "improve OCR accuracy on small text at the cost of processing time."
        ),
    )
    ocr_psm = fields.Integer(
        string="Page Segmentation Mode",
        default=6,
        required=True,
        help=(
            "Tesseract '--psm' page segmentation mode. Mode 6 assumes a single "
            "uniform block of text and works well for tabular bank statement "
            "pages. Adjust per template if OCR output is poorly structured."
        ),
    )
    currency_id = fields.Many2one(
        string="Default Currency",
        comodel_name="res.currency",
        help=(
            "Fallback currency used when the parser code does not set "
            "result['currency_code']. If both this field and the parser code "
            "omit the currency, the import will fail with a missing currency error."
        ),
    )
    parser_code = fields.Text(
        string="Parser Code",
        required=True,
        help=(
            "Python code executed inside safe_eval to transform OCR-extracted "
            "PDF content into bank statement data. "
            "Available input variables: "
            "pages (list[str] — OCR text per PDF page), "
            "full_text (str — all pages joined by newline), "
            "tables (list — always empty, reserved for parity with sibling "
            "parser patterns), "
            "filename (str), re (module), datetime (module), date (datetime.date), "
            "mapping (this record). "
            "Required output: set result['statements'] to a non-empty list of statement "
            "dicts, each with a 'transactions' key containing dicts with at minimum: "
            "date (str YYYY-MM-DD), amount (float), payment_ref (str), "
            "unique_import_id (str). "
            "Optional output: result['currency_code'] (str ISO 4217), "
            "result['account_number'] (str or None)."
        ),
    )
    preprocess_enabled = fields.Boolean(
        string="Enable Image Preprocessing",
        default=False,
        help=(
            "Master toggle for image preprocessing before OCR. When disabled, "
            "each rendered page is passed to OCR as-is (existing behavior). "
            "Enable this for low-quality scans (e.g. photocopied passbooks) "
            "where OCR text comes out too noisy for parser_code to parse."
        ),
    )
    preprocess_grayscale = fields.Boolean(
        string="Grayscale",
        default=True,
        help=(
            "Convert the rendered page to a single-channel grayscale image "
            "before further preprocessing steps. Only applied when "
            "'Enable Image Preprocessing' is active."
        ),
    )
    preprocess_autocontrast = fields.Boolean(
        string="Auto Contrast",
        default=True,
        help=(
            "Normalize pixel intensity to the full 0-255 range to improve "
            "contrast on faded or unevenly lit scans. Only applied when "
            "'Enable Image Preprocessing' is active."
        ),
    )
    preprocess_binarize = fields.Selection(
        string="Binarization",
        selection=[
            ("none", "None"),
            ("global", "Global threshold"),
            ("otsu", "Otsu"),
            ("adaptive", "Adaptive"),
        ],
        default="adaptive",
        help=(
            "Method used to convert the grayscale image into pure black-and-"
            "white pixels before OCR. 'Adaptive' is recommended for scans "
            "with uneven lighting or folds (e.g. passbook photos): "
            "'None' = skip binarization, "
            "'Global threshold' = single fixed threshold value ('Threshold' "
            "field below), "
            "'Otsu' = automatic single threshold computed from the image "
            "histogram, "
            "'Adaptive' = local threshold computed per image region. "
            "Only applied when 'Enable Image Preprocessing' is active."
        ),
    )
    preprocess_threshold = fields.Integer(
        string="Threshold",
        default=128,
        help=(
            "Pixel intensity threshold (0-255) used only when 'Binarization' "
            "is set to 'Global threshold'. Pixels above this value become "
            "white, pixels at or below become black."
        ),
    )
    preprocess_deskew = fields.Boolean(
        string="Deskew",
        default=False,
        help=(
            "Automatically detect and correct the rotation angle of a "
            "slightly tilted scan before OCR. Only applied when "
            "'Enable Image Preprocessing' is active."
        ),
    )
    preprocess_scale = fields.Float(
        string="Upscale Factor",
        default=1.0,
        help=(
            "Factor used to resize the rendered page before other "
            "preprocessing steps, e.g. 2.0 doubles width and height. Values "
            "greater than 1.0 can help OCR read small text on low-resolution "
            "scans. Only applied when 'Enable Image Preprocessing' is active."
        ),
    )

    def _preprocess_image(self, image):
        """Apply configured OpenCV preprocessing steps to a rendered page.

        Pure seam for testing: accepts and returns a PIL Image, no OCR or
        PDF rendering involved.
        """
        self.ensure_one()
        arr = numpy.array(image)

        if self.preprocess_scale and self.preprocess_scale != 1.0:
            arr = cv2.resize(
                arr,
                None,
                fx=self.preprocess_scale,
                fy=self.preprocess_scale,
                interpolation=cv2.INTER_CUBIC,
            )

        needs_grayscale = (
            self.preprocess_grayscale or self.preprocess_binarize != "none"
        )
        if needs_grayscale and arr.ndim == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        if self.preprocess_autocontrast:
            arr = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX)

        if self.preprocess_binarize == "global":
            _thresh, arr = cv2.threshold(
                arr, self.preprocess_threshold, 255, cv2.THRESH_BINARY
            )
        elif self.preprocess_binarize == "otsu":
            _thresh, arr = cv2.threshold(
                arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        elif self.preprocess_binarize == "adaptive":
            arr = cv2.adaptiveThreshold(
                arr,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                15,
            )

        if self.preprocess_deskew:
            arr = self._preprocess_deskew(arr)

        return Image.fromarray(arr)

    def _preprocess_deskew(self, arr):
        """Estimate and correct the rotation angle of a binarized image.

        Returns the input array unchanged if no non-zero pixels are found
        (e.g. a blank page), instead of raising.
        """
        inverted = 255 - arr
        coords = cv2.findNonZero(inverted)
        if coords is None:
            return arr

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle

        height, width = arr.shape[:2]
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

    def _extract(self, data_file):
        """Extract OCR text per page from PDF binary data using Tesseract."""
        self.ensure_one()
        try:
            import pdf2image
            import pytesseract
        except ImportError:
            error_message = (
                _(
                    """
Context: OCR-extract text from a scanned PDF file for bank statement import
Database ID: %s
Problem: Python library 'pytesseract' and/or 'pdf2image' is not installed
Solution: Install both by adding 'pytesseract' and 'pdf2image' to \
odoo/custom/dependencies/pip.txt, add 'tesseract-ocr' and 'poppler-utils' to \
odoo/custom/dependencies/apt.txt, then rebuild the Odoo image (invoke img_build)
"""
                )
                % self.id
            )
            raise UserError(error_message)

        try:
            images = pdf2image.convert_from_bytes(data_file, dpi=self.ocr_dpi)
            pages = [
                pytesseract.image_to_string(
                    self._preprocess_image(image) if self.preprocess_enabled else image,
                    lang=self.ocr_lang,
                    config="--psm %d" % self.ocr_psm,
                )
                for image in images
            ]
        except Exception as e:
            error_message = (
                _(
                    """
Context: OCR-extract text from a scanned PDF file for bank statement import
Database ID: %s
Problem: OCR extraction failed: %s
Solution: Ensure 'tesseract-ocr' and 'poppler-utils' system binaries are \
installed on the Odoo image (odoo/custom/dependencies/apt.txt), and that the \
uploaded file is a valid PDF
"""
                )
                % (self.id, str(e))
            )
            raise UserError(error_message)

        return {
            "pages": pages,
            "full_text": "\n".join(pages),
        }

    def _parse_extracted(self, extracted, filename):
        """Execute parser_code against OCR-extracted PDF content.

        This is the pure seam for testing: accepts a pre-extracted dict
        (no PDF binary or OCR engine needed) and returns the statement
        import triplet.
        """
        self.ensure_one()
        import datetime as dt_module
        import re as re_module

        eval_context = {
            "pages": extracted.get("pages", []),
            "full_text": extracted.get("full_text", ""),
            "tables": extracted.get("tables", []),
            "filename": filename,
            "datetime": wrap_module(
                dt_module, ["date", "datetime", "timedelta", "timezone"]
            ),
            "date": dt_module.date,
            "re": wrap_module(
                re_module,
                [
                    "compile",
                    "search",
                    "match",
                    "findall",
                    "sub",
                    "split",
                    "IGNORECASE",
                    "MULTILINE",
                    "DOTALL",
                    "I",
                    "M",
                    "S",
                ],
            ),
            "mapping": self,
            "result": {},
        }

        try:
            safe_eval(self.parser_code, eval_context, mode="exec", nocopy=True)
        except Exception as e:
            error_message = (
                _(
                    """
Context: Execute PDF image parser code for bank statement import
Database ID: %s
Problem: Parser code execution failed: %s
Solution: Fix the parser_code syntax errors or logic issues shown in the problem above
"""
                )
                % (self.id, str(e))
            )
            raise UserError(error_message)

        parsed = eval_context.get("result", {})
        statements = parsed.get("statements")

        if not statements:
            error_message = (
                _(
                    """
Context: Parse scanned PDF bank statement
Database ID: %s
Problem: Parser code produced empty or missing result["statements"]
Solution: Ensure parser_code sets result["statements"] to a non-empty list of \
statement dicts, each containing a "transactions" list
"""
                )
                % self.id
            )
            raise UserError(error_message)

        currency_code = parsed.get("currency_code") or (
            self.currency_id.name if self.currency_id else False
        )
        account_number = parsed.get("account_number")
        return (currency_code, account_number, statements)

    def parse(self, data_file, filename):
        """Full parse pipeline: OCR-extract PDF content then run parser_code."""
        self.ensure_one()
        return self._parse_extracted(self._extract(data_file), filename)

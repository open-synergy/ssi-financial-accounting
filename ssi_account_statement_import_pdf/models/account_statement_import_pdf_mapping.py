# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, wrap_module


class AccountStatementImportPdfMapping(models.Model):
    _name = "account.statement.import.pdf.mapping"
    _inherit = ["mixin.master_data"]
    _description = "PDF Statement Mapping"

    extraction_mode = fields.Selection(
        string="Extraction Mode",
        selection=[
            ("text", "Text (full-page text)"),
            ("tables", "Tables (structured rows)"),
        ],
        default="text",
        required=True,
        help=(
            "Choose 'Text' to extract raw text per page via pdfplumber.extract_text(). "
            "Choose 'Tables' to extract structured table data via pdfplumber.extract_tables(). "
            "The chosen mode determines which variables (full_text/pages vs tables) "
            "are populated in the parser_code context."
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
            "Python code executed inside safe_eval to transform extracted PDF content "
            "into bank statement data. "
            "Available input variables: "
            "pages (list[str] — one entry per PDF page, text mode), "
            "full_text (str — all pages joined by newline, text mode), "
            "tables (list[list[list]] — extracted tables, tables mode), "
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

    def _extract(self, data_file):
        """Extract text or tables from PDF binary data using pdfplumber."""
        self.ensure_one()
        try:
            import pdfplumber
        except ImportError:
            error_message = (
                _(
                    """
Context: Extract text from PDF file for bank statement import
Database ID: %s
Problem: Python library 'pdfplumber' is not installed
Solution: Install pdfplumber by adding it to your Odoo image dependencies \
(e.g. add 'pdfplumber' to odoo/custom/dependencies/pip.txt)
"""
                )
                % self.id
            )
            raise UserError(error_message)

        pages = []
        tables = []
        with pdfplumber.open(io.BytesIO(data_file)) as pdf:
            for page in pdf.pages:
                if self.extraction_mode == "text":
                    pages.append(page.extract_text() or "")
                else:
                    page_tables = page.extract_tables() or []
                    tables.extend(page_tables)

        return {
            "pages": pages,
            "full_text": "\n".join(pages),
            "tables": tables,
        }

    def _parse_extracted(self, extracted, filename):
        """Execute parser_code against extracted PDF content.

        This is the pure seam for testing: accepts a pre-extracted dict
        (no PDF binary needed) and returns the statement import triplet.
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
Context: Execute PDF parser code for bank statement import
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
Context: Parse PDF bank statement
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
        """Full parse pipeline: extract PDF content then run parser_code."""
        self.ensure_one()
        return self._parse_extracted(self._extract(data_file), filename)

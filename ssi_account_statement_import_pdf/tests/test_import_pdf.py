# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

# Parser code for CRUD and pure-seam tests:
# reads "Account: ..." and "Currency: ..." headers then "date | amount | ref" lines.
_PARSER_CODE = """\
lines = [l.strip() for l in full_text.strip().splitlines() if l.strip()]
account_number = None
currency_code = None
transactions = []

for line in lines:
    if line.startswith("Account:"):
        account_number = line.split(":", 1)[1].strip()
    elif line.startswith("Currency:"):
        currency_code = line.split(":", 1)[1].strip()
    elif "|" in line:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            date_str, amount_str, ref = parts[0], parts[1], parts[2]
            transactions.append({
                "date": date_str,
                "amount": float(amount_str),
                "payment_ref": ref,
                "unique_import_id": "%s-%s-%s" % (account_number or "NA", date_str, ref),
            })

result["currency_code"] = currency_code
result["account_number"] = account_number
result["statements"] = [{"name": "STMT-001", "transactions": transactions}]
"""


@tagged("post_install", "-at_install")
class TestImportPdf(TransactionCase):
    def setUp(self):
        super().setUp()
        self.mapping = self.env["account.statement.import.pdf.mapping"].create(
            {
                "name": "Test PDF Mapping",
                "code": "TEST-IMPORT",
                "extraction_mode": "text",
                "parser_code": _PARSER_CODE,
            }
        )
        # Find a bank journal for end-to-end wizard tests.
        self.bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        # Use company's default currency so _match_journal can find the journal.
        self.company_currency = self.env.company.currency_id.name

    @staticmethod
    def _make_extracted(account="1234567890", currency="IDR"):
        """Build a pre-extracted dict matching the parser contract (no PDF needed)."""
        text = (
            "Account: %s\n"
            "Currency: %s\n"
            "2026-01-05 | 500000.0 | TRANSFER MASUK TEST 1\n"
            "2026-01-10 | -200000.0 | PEMBAYARAN TEST 2\n"
        ) % (account, currency)
        return {"pages": [text], "full_text": text, "tables": []}

    @staticmethod
    def _make_sample_pdf(text_lines):
        """Create a minimal valid PDF with extractable text using Type1/Helvetica font.

        Uses the standard 14 PDF fonts so pdfplumber can map character codes
        without needing an embedded font program.
        """
        stream_parts = ["BT /F1 10 Tf 72 720 Td"]
        for line in text_lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_parts.append("(%s) Tj 0 -14 Td" % escaped)
        stream_parts.append("ET")
        content = "\n".join(stream_parts).encode("latin-1")

        objs = [
            b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n",
            b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n",
            (
                b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
                b" /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>>\nendobj\n"
            ),
            (
                ("4 0 obj\n<</Length %d>>\nstream\n" % len(content)).encode()
                + content
                + b"\nendstream\nendobj\n"
            ),
            b"5 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>\nendobj\n",
        ]

        pdf = b"%PDF-1.4\n"
        offsets = []
        for obj in objs:
            offsets.append(len(pdf))
            pdf += obj

        xref = len(pdf)
        pdf += b"xref\n"
        pdf += ("%d %d\n" % (0, len(objs) + 1)).encode()
        pdf += b"0000000000 65535 f \n"
        for off in offsets:
            pdf += ("%010d 00000 n \n" % off).encode()
        pdf += (
            "trailer\n<</Size %d /Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, xref)
        ).encode()
        return pdf

    def test_parse_extracted_returns_triplet(self):
        """_parse_extracted returns (currency_code, account_number, statements) triplet."""
        extracted = self._make_extracted(account="9876543210", currency="USD")
        result = self.mapping._parse_extracted(extracted, "statement.pdf")

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

        currency_code, account_number, statements = result
        self.assertEqual(currency_code, "USD")
        self.assertEqual(account_number, "9876543210")
        self.assertTrue(statements, "statements must not be empty")

        transactions = statements[0]["transactions"]
        self.assertEqual(len(transactions), 2, "expected 2 transactions")
        self.assertEqual(transactions[0]["amount"], 500000.0)
        self.assertEqual(transactions[1]["amount"], -200000.0)
        self.assertEqual(transactions[0]["payment_ref"], "TRANSFER MASUK TEST 1")

    def test_import_pdf_creates_statement(self):
        """Wizard with pdf_mapping_id parses PDF and creates bank statement lines."""
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")

        pdf_bytes = self._make_sample_pdf(
            [
                # No "Account:" line — account_number stays None, matches any bank journal.
                "Currency: %s" % self.company_currency,
                "2026-03-01 | 500000.0 | PDF IMPORT TEST TXN 1",
                "2026-03-02 | -200000.0 | PDF IMPORT TEST TXN 2",
            ]
        )
        wizard = (
            self.env["account.statement.import"]
            .with_context(journal_id=self.bank_journal.id)
            .create(
                {
                    "statement_file": base64.b64encode(pdf_bytes),
                    "statement_filename": "bank_statement.pdf",
                    "pdf_mapping_id": self.mapping.id,
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
                len(lines), 2, "expected at least 2 statement lines after PDF import"
            )

    def test_import_pdf_dedup(self):
        """Second import of the same PDF raises UserError (all lines already imported).

        OCA's dedup mechanism tracks unique_import_id per statement line.  When
        every transaction in the file already exists, the wizard raises UserError
        instead of silently skipping — this is the expected OCA behaviour.
        The test verifies that after two attempts, exactly 2 lines exist (no dups).
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")

        pdf_bytes = self._make_sample_pdf(
            [
                "Currency: %s" % self.company_currency,
                "2026-04-01 | 111111.0 | DEDUP TEST TXN A",
                "2026-04-02 | 222222.0 | DEDUP TEST TXN B",
            ]
        )
        encoded = base64.b64encode(pdf_bytes)

        import_env = self.env["account.statement.import"].with_context(
            journal_id=self.bank_journal.id
        )
        wizard1 = import_env.create(
            {
                "statement_file": encoded,
                "statement_filename": "dedup.pdf",
                "pdf_mapping_id": self.mapping.id,
            }
        )
        wizard1.import_file_button()

        wizard2 = import_env.create(
            {
                "statement_file": encoded,
                "statement_filename": "dedup.pdf",
                "pdf_mapping_id": self.mapping.id,
            }
        )
        # Second import: all unique_import_ids already exist → UserError, no new lines.
        with self.assertRaises(UserError):
            wizard2.import_file_button()

        # OCA prefixes journal.id to unique_import_id, so search by payment_ref instead.
        lines = self.env["account.bank.statement.line"].search(
            [("payment_ref", "in", ["DEDUP TEST TXN A", "DEDUP TEST TXN B"])]
        )
        self.assertEqual(
            len(lines), 2, "deduplication failed: expected exactly 2 lines"
        )

    def test_parse_file_fallback_non_pdf(self):
        """When filename does not end in .pdf, _parse_file calls super() not PDF mapping."""
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(b"dummy content"),
                "statement_filename": "statement.csv",
                "pdf_mapping_id": self.mapping.id,
            }
        )
        # pdf_mapping_id is set but filename ends in .csv so PDF branch is skipped.
        # super()._parse_file() raises UserError for unrecognised format.
        with self.assertRaises(UserError):
            wizard._parse_file(b"dummy content")

    def test_parse_extracted_empty_raises(self):
        """_parse_extracted raises UserError when parser_code yields empty statements."""
        empty_mapping = self.env["account.statement.import.pdf.mapping"].create(
            {
                "name": "Empty Parser Mapping",
                "code": "EMPTY-PARSE-TEST",
                "extraction_mode": "text",
                "parser_code": "result['statements'] = []",
            }
        )
        extracted = self._make_extracted()
        with self.assertRaises(UserError):
            empty_mapping._parse_extracted(extracted, "test.pdf")

    def test_parser_code_requires_technical_group(self):
        """A user without the configurator group cannot create PDF mapping records."""
        demo_user = self.env.ref("base.user_demo")
        with self.assertRaises(AccessError):
            self.env["account.statement.import.pdf.mapping"].with_user(
                demo_user
            ).create(
                {
                    "name": "Unauthorized Mapping",
                    "code": "UNAUTH-TEST",
                    "extraction_mode": "text",
                    "parser_code": "result['statements'] = []",
                }
            )

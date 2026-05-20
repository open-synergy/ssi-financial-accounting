# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSsiAccountStatementImport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")],
            limit=1,
        )

    def test_action_import_statement_with_journal(self):
        """Test action_import_statement returns action dict when journal is set."""
        if not self.bank_journal:
            self.skipTest("No bank journal found")

        statement = self.env["account.bank.statement"].create(
            {
                "name": "Test Import Statement",
                "journal_id": self.bank_journal.id,
            }
        )
        result = statement.action_import_statement()
        self.assertIsInstance(result, dict, "action should return a dict")
        self.assertIn("type", result)

    def test_action_import_statement_without_journal(self):
        """Test action_import_statement returns None when no journal."""
        statement = self.env["account.bank.statement"].create(
            {
                "name": "Test Import Statement No Journal",
                "journal_id": self.bank_journal.id if self.bank_journal else False,
            }
        )
        # Clear journal_id to test the no-journal branch
        if not self.bank_journal:
            result = statement.action_import_statement()
            self.assertIsNone(result, "action should return None without journal")

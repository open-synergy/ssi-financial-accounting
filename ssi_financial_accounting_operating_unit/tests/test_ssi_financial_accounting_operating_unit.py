# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSsiFinancialAccountingOperatingUnit(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.operating_unit = self.env["operating.unit"].search(
            [("company_id", "=", self.company.id)],
            limit=1,
        )

    def test_account_journal_has_operating_unit_ids(self):
        """Test that account.journal has operating_unit_ids field."""
        journal = self.env["account.journal"].search([], limit=1)
        if not journal:
            self.skipTest("No journals found")
        fields_info = journal.fields_get(["operating_unit_ids"])
        self.assertIn("operating_unit_ids", fields_info)

    def test_account_move_has_operating_unit_id(self):
        """Test that account.move has operating_unit_id field."""
        move = self.env["account.move"].search([], limit=1)
        if not move:
            self.skipTest("No account moves found")
        fields_info = move.fields_get(["operating_unit_id"])
        self.assertIn("operating_unit_id", fields_info)

    def test_account_move_line_has_operating_unit_id(self):
        """Test that account.move.line has operating_unit_id field."""
        move_line = self.env["account.move.line"].search([], limit=1)
        if not move_line:
            self.skipTest("No move lines found")
        fields_info = move_line.fields_get(["operating_unit_id"])
        self.assertIn("operating_unit_id", fields_info)

    def test_account_bank_statement_has_operating_unit_id(self):
        """Test that account.bank.statement has operating_unit_id field."""
        model = self.env["account.bank.statement"]
        fields_info = model.fields_get(["operating_unit_id"])
        self.assertIn("operating_unit_id", fields_info)

    def test_create_move_without_ou(self):
        """Test creating account move without operating unit works."""
        journal = self.env["account.journal"].search(
            [("type", "=", "general")], limit=1
        )
        if not journal:
            self.skipTest("No general journal found")
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
            }
        )
        self.assertEqual(move.state, "draft")

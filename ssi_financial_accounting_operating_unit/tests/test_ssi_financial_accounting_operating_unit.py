# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
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

    def test_bank_statement_line_ou_via_delegation_not_mixin(self):
        """Regression: account.bank.statement.line gets operating_unit_id via
        _inherits delegation from account.move — NOT from mixin.single_operating_unit.
        Adding the mixin would break the delegation field. This test verifies the field
        exists via delegation.
        """
        model = self.env["account.bank.statement.line"]

        # Field must exist (via delegation from account.move)
        fields_info = model.fields_get(["operating_unit_id"])
        self.assertIn("operating_unit_id", fields_info)

        # The field originates from account.move via _inherits delegation,
        # so it must NOT be declared as a local field on the model itself.
        local_fields = model._fields
        local_field = local_fields.get("operating_unit_id")
        # A delegated field has model_name pointing to the delegated model
        self.assertEqual(
            local_field.related_field.model_name if local_field else None,
            "account.move",
            "operating_unit_id on account.bank.statement.line must be a "
            "delegation field originating from account.move, not a mixin field.",
        )

    def test_bank_statement_line_ou_propagated_from_statement(self):
        """Regression: creating a bank.statement.line should carry the OU of the
        parent bank.statement when OU is set on the statement.
        """
        journal = self.env["account.journal"].search([("type", "=", "bank")], limit=1)
        if not journal or not self.operating_unit:
            self.skipTest("No bank journal or operating unit found")

        statement = self.env["account.bank.statement"].create(
            {
                "name": "Test OU Propagation",
                "journal_id": journal.id,
                "operating_unit_id": self.operating_unit.id,
            }
        )
        self.assertEqual(statement.operating_unit_id, self.operating_unit)

        line = self.env["account.bank.statement.line"].create(
            {
                "statement_id": statement.id,
                "payment_ref": "Test Line OU",
                "amount": 100.0,
                "date": fields.Date.today(),
            }
        )
        self.assertEqual(
            line.operating_unit_id,
            self.operating_unit,
            "bank.statement.line.operating_unit_id must equal the parent "
            "statement's operating_unit_id (propagated via create() override, "
            "stored on account.move via delegation).",
        )

    def test_account_payment_ou_via_delegation(self):
        """Regression: account.payment exposes operating_unit_id via
        _inherits delegation to account.move (same pattern as
        bank.statement.line, BL-0003) — NOT via mixin.single_operating_unit
        added directly to account.payment.
        """
        model = self.env["account.payment"]

        fields_info = model.fields_get(["operating_unit_id"])
        self.assertIn("operating_unit_id", fields_info)

        local_field = model._fields.get("operating_unit_id")
        self.assertEqual(
            local_field.related_field.model_name if local_field else None,
            "account.move",
            "operating_unit_id on account.payment must be a delegation "
            "field originating from account.move, not a mixin field.",
        )

        journal = self.env["account.journal"].search(
            [("type", "in", ("bank", "cash"))], limit=1
        )
        partner = self.env["res.partner"].search([], limit=1)
        if not journal or not partner or not self.operating_unit:
            self.skipTest("No journal/partner/operating unit found")

        payment = self.env["account.payment"].create(
            {
                "journal_id": journal.id,
                "partner_id": partner.id,
                "amount": 100.0,
                "operating_unit_id": self.operating_unit.id,
            }
        )
        self.assertEqual(
            payment.operating_unit_id,
            self.operating_unit,
            "Setting operating_unit_id on account.payment must persist via "
            "delegation to the underlying account.move (move_id).",
        )
        self.assertEqual(
            payment.move_id.operating_unit_id,
            self.operating_unit,
            "account.payment.operating_unit_id must delegate to move_id.",
        )

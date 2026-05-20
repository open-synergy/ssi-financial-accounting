# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSsiAccountCreateLiquidityJournal(TransactionCase):
    def setUp(self):
        super().setUp()
        account_type = self.env["account.account.type"].create(
            {
                "name": "Test Liquidity Type",
                "type": "liquidity",
                "internal_group": "asset",
            }
        )
        self.cash_account = self.env["account.account"].create(
            {
                "name": "Test Cash Account",
                "code": "TESTCASH01",
                "user_type_id": account_type.id,
                "reconcile": False,
            }
        )
        self.suspense_account = self.env["account.account"].create(
            {
                "name": "Test Suspense Account",
                "code": "TESTSUSP01",
                "user_type_id": account_type.id,
                "reconcile": False,
            }
        )

    def test_create_cash_journal(self):
        """Test creating a cash journal from an account."""
        wizard = (
            self.env["account.wizard_create_liquidity_journal"]
            .with_context(active_ids=[self.cash_account.id])
            .create(
                {
                    "liquidity_type": "cash",
                    "two_step": False,
                    "suspense_account_id": self.suspense_account.id,
                }
            )
        )
        wizard.with_context(active_ids=[self.cash_account.id]).action_confirm()

        journal = self.env["account.journal"].search(
            [
                ("name", "=", self.cash_account.name),
                ("type", "=", "cash"),
            ],
            limit=1,
        )
        self.assertTrue(journal, "Cash journal should have been created")
        self.assertEqual(journal.default_account_id, self.cash_account)

    def test_create_bank_journal_two_step(self):
        """Test creating a bank journal with two-step reconciliation."""
        wizard = (
            self.env["account.wizard_create_liquidity_journal"]
            .with_context(active_ids=[self.cash_account.id])
            .create(
                {
                    "liquidity_type": "bank",
                    "two_step": True,
                    "suspense_account_id": self.suspense_account.id,
                }
            )
        )
        wizard.with_context(active_ids=[self.cash_account.id]).action_confirm()

        journal = self.env["account.journal"].search(
            [
                ("name", "=", self.cash_account.name),
                ("type", "=", "bank"),
            ],
            limit=1,
        )
        self.assertTrue(journal, "Bank journal should have been created")
        self.assertEqual(journal.payment_debit_account_id, self.suspense_account)
        self.assertEqual(journal.payment_credit_account_id, self.suspense_account)

    def test_no_active_ids(self):
        """Test wizard with no active_ids does not create journals."""
        initial_count = self.env["account.journal"].search_count([])
        wizard = self.env["account.wizard_create_liquidity_journal"].create(
            {
                "liquidity_type": "cash",
                "two_step": False,
                "suspense_account_id": self.suspense_account.id,
            }
        )
        wizard.action_confirm()
        final_count = self.env["account.journal"].search_count([])
        self.assertEqual(initial_count, final_count, "No journals should be created")

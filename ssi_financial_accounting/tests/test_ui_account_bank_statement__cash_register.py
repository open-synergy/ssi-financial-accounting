# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# HttpSavepointCase -- NOT HttpCase. See odoo-development-ui-test skill,
# structure-and-runner.md "Base class" -- HttpCase in 14.0 does not set up
# cls.env in setUpClass.
from odoo.tests import HttpSavepointCase, tagged


@tagged("post_install", "-at_install")
class TestUiAccountBankStatementCashRegister(HttpSavepointCase):
    """Tour tests for the Cash Register variant of ``account.bank.statement``.

    IK source: ``docs/account_bank_statement__cash_register/``. Fixtures use
    a dedicated journal per tour so each tour's Pre-Condition record is
    unambiguous in the list view, and set ``state``/``is_reconciled``
    directly where the IK Pre-Condition only requires the record to already
    be in that status -- reaching it through the full business flow is
    covered by the ``04-post``/``05-validate`` tours themselves.
    """

    @classmethod
    def setUpClass(cls):
        """Create the journals, statements, and access rights the tours need."""
        super().setUpClass()
        # user_id is explicit below because cls.env runs as SUPERUSER, and
        # the tour logs in as "admin" over HTTP -- a real, non-superuser
        # session subject to groups and record rules.
        cls.admin = cls.env.ref("base.user_admin")
        cls.admin.write(
            {"groups_id": [(4, cls.env.ref("account.group_account_user").id)]}
        )

        # Take Money In/Out (09-take-money-in-out.md) requires the company's
        # Internal Transfer Account to be configured.
        cls.transfer_account = cls.env["account.account"].create(
            {
                "name": "Tour Transfer Account",
                "code": "TOURXFER",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_current_assets"
                ).id,
                "reconcile": True,
            }
        )
        cls.env.company.transfer_account_id = cls.transfer_account.id

        cls.journal_create = cls.env["account.journal"].create(
            {"name": "Tour Cash Register Create", "type": "cash", "code": "TCRCR"}
        )

        cls.journal_post = cls.env["account.journal"].create(
            {"name": "Tour Cash Register Post", "type": "cash", "code": "TCRPO"}
        )
        cls.statement_post = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_post.id}
        )
        cls.env["account.bank.statement.line"].create(
            {
                "statement_id": cls.statement_post.id,
                "payment_ref": "Tour Test Line",
                "amount": 100.0,
            }
        )

        # ``is_reconciled`` is a stored compute (account/models/
        # account_bank_statement.py `_compute_is_reconciled`) with no
        # inverse: writing it directly gets silently overwritten by the
        # next recompute. To make the Validate fixture's line genuinely
        # reconciled without exercising full manual reconciliation (out of
        # scope for a UI tour), its counterpart move line is created
        # against a real account instead of the journal's suspense
        # account -- ``_seek_for_lines`` then buckets it as an "other"
        # line, so ``_compute_is_reconciled`` takes the
        # "no suspense line left" branch and sets ``is_reconciled = True``
        # on its own.
        cls.reconcile_account = cls.env["account.account"].create(
            {
                "name": "Tour Reconciled Counterpart",
                "code": "TOURCRRC",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_current_assets"
                ).id,
                "reconcile": True,
            }
        )

        cls.journal_validate = cls.env["account.journal"].create(
            {"name": "Tour Cash Register Validate", "type": "cash", "code": "TCRVA"}
        )
        cls.statement_validate = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_validate.id}
        )
        cls.env["account.bank.statement.line"].create(
            {
                "statement_id": cls.statement_validate.id,
                "payment_ref": "Tour Test Line",
                "amount": 100.0,
                "counterpart_account_id": cls.reconcile_account.id,
            }
        )
        # Ending Balance is aligned with the computed balance so the
        # difference is zero: for a cash journal, a non-zero difference
        # opens the closing-balance confirmation wizard instead of
        # validating directly (see button_validate_or_action).
        cls.statement_validate.write({"state": "posted", "balance_end_real": 100.0})
        # Regression guard: if the fixture above stops producing a fully
        # reconciled statement, `validate_ok` goes False and the
        # ``test_validate`` tour times out on an invisible Validate button
        # instead of failing here with a clear message.
        assert (
            cls.statement_validate.validate_ok
        ), "Validate fixture is not reconciled: validate_ok is False"

        cls.journal_reset_new = cls.env["account.journal"].create(
            {"name": "Tour Cash Register Reset New", "type": "cash", "code": "TCRRN"}
        )
        cls.statement_reset_new = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_reset_new.id}
        )
        cls.statement_reset_new.write({"state": "posted"})

        cls.journal_reset_processing = cls.env["account.journal"].create(
            {
                "name": "Tour Cash Register Reset Processing",
                "type": "cash",
                "code": "TCRRP",
            }
        )
        cls.statement_reset_processing = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_reset_processing.id}
        )
        cls.statement_reset_processing.write({"state": "confirm"})

        cls.journal_print = cls.env["account.journal"].create(
            {"name": "Tour Cash Register Print", "type": "cash", "code": "TCRPR"}
        )
        cls.statement_print = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_print.id}
        )

        cls.journal_take_money = cls.env["account.journal"].create(
            {"name": "Tour Cash Register Take Money", "type": "cash", "code": "TCRTM"}
        )
        cls.statement_take_money = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_take_money.id}
        )

        cls.journal_count = cls.env["account.journal"].create(
            {"name": "Tour Cash Register Count", "type": "cash", "code": "TCRCT"}
        )
        cls.statement_count = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_count.id}
        )

    def test_create(self):
        """Run the create tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/01-create.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register_create",
            login="admin",
        )

    def test_post(self):
        """Run the post tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/04-post.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register_post",
            login="admin",
        )

    def test_validate(self):
        """Run the validate tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/05-validate.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register_validate",
            login="admin",
        )

    def test_reset_to_new(self):
        """Run the reset-to-new tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/06-reset-to-new.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register"
            "_reset_to_new",
            login="admin",
        )

    def test_reset_to_processing(self):
        """Run the reset-to-processing tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/07-reset-to-processing.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register"
            "_reset_to_processing",
            login="admin",
        )

    def test_print(self):
        """Run the print tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/08-print.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register_print",
            login="admin",
        )

    def test_take_money_in_out(self):
        """Run the Take Money In/Out tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/09-take-money-in-out.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register"
            "_take_money_in_out",
            login="admin",
        )

    def test_count(self):
        """Run the Count tour for the Cash Register variant.

        IK: docs/account_bank_statement__cash_register/10-count.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_cash_register_count",
            login="admin",
        )

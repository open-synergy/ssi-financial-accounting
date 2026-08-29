# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# HttpSavepointCase -- NOT HttpCase. See odoo-development-ui-test skill,
# structure-and-runner.md "Base class" -- HttpCase in 14.0 does not set up
# cls.env in setUpClass.
from odoo.tests import HttpSavepointCase, tagged


@tagged("post_install", "-at_install")
class TestUiAccountBankStatementBankStatement(HttpSavepointCase):
    """Tour tests for the Bank Statement variant of ``account.bank.statement``.

    IK source: ``docs/account_bank_statement__bank_statement/``. Fixtures use
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

        cls.journal_create = cls.env["account.journal"].create(
            {"name": "Tour Bank Statement Create", "type": "bank", "code": "TBSCR"}
        )

        cls.journal_post = cls.env["account.journal"].create(
            {"name": "Tour Bank Statement Post", "type": "bank", "code": "TBSPO"}
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

        cls.journal_validate = cls.env["account.journal"].create(
            {"name": "Tour Bank Statement Validate", "type": "bank", "code": "TBSVA"}
        )
        cls.statement_validate = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_validate.id}
        )
        line_validate = cls.env["account.bank.statement.line"].create(
            {
                "statement_id": cls.statement_validate.id,
                "payment_ref": "Tour Test Line",
                "amount": 100.0,
            }
        )
        # Force the line to appear reconciled -- real reconciliation is out
        # of scope for a UI tour; the tour only exercises the Validate
        # button once the Pre-Condition is met.
        line_validate.is_reconciled = True
        cls.statement_validate.write({"state": "posted"})

        cls.journal_reset_new = cls.env["account.journal"].create(
            {"name": "Tour Bank Statement Reset New", "type": "bank", "code": "TBSRN"}
        )
        cls.statement_reset_new = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_reset_new.id}
        )
        cls.statement_reset_new.write({"state": "posted"})

        cls.journal_reset_processing = cls.env["account.journal"].create(
            {
                "name": "Tour Bank Statement Reset Processing",
                "type": "bank",
                "code": "TBSRP",
            }
        )
        cls.statement_reset_processing = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_reset_processing.id}
        )
        cls.statement_reset_processing.write({"state": "confirm"})

        cls.journal_print = cls.env["account.journal"].create(
            {"name": "Tour Bank Statement Print", "type": "bank", "code": "TBSPR"}
        )
        cls.statement_print = cls.env["account.bank.statement"].create(
            {"journal_id": cls.journal_print.id}
        )

    def test_create(self):
        """Run the create tour for the Bank Statement variant.

        IK: docs/account_bank_statement__bank_statement/01-create.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_bank_statement_create",
            login="admin",
        )

    def test_post(self):
        """Run the post tour for the Bank Statement variant.

        IK: docs/account_bank_statement__bank_statement/04-post.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_bank_statement_post",
            login="admin",
        )

    def test_validate(self):
        """Run the validate tour for the Bank Statement variant.

        IK: docs/account_bank_statement__bank_statement/05-validate.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_bank_statement_validate",
            login="admin",
        )

    def test_reset_to_new(self):
        """Run the reset-to-new tour for the Bank Statement variant.

        IK: docs/account_bank_statement__bank_statement/06-reset-to-new.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_bank_statement"
            "_reset_to_new",
            login="admin",
        )

    def test_reset_to_processing(self):
        """Run the reset-to-processing tour for the Bank Statement variant.

        IK: docs/account_bank_statement__bank_statement/07-reset-to-processing.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_bank_statement"
            "_reset_to_processing",
            login="admin",
        )

    def test_print(self):
        """Run the print tour for the Bank Statement variant.

        IK: docs/account_bank_statement__bank_statement/08-print.md
        """
        self.start_tour(
            "/web",
            "ssi_financial_accounting_account_bank_statement_bank_statement_print",
            login="admin",
        )

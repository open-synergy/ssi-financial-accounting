# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSsiAccountMovePy3oReport(TransactionCase):
    def test_module_installed(self):
        """Verify ssi_account_move_py3o_report is installed."""
        module = self.env["ir.module.module"].search(
            [
                ("name", "=", "ssi_account_move_py3o_report"),
                ("state", "=", "installed"),
            ],
            limit=1,
        )
        self.assertTrue(module, "ssi_account_move_py3o_report should be installed")

    def test_account_move_report_action_exists(self):
        """Verify the py3o report action is registered for account.move."""
        reports = self.env["ir.actions.report"].search(
            [("model", "=", "account.move"), ("report_type", "=", "py3o")],
            limit=1,
        )
        self.assertTrue(
            reports,
            "At least one py3o report for account.move should exist",
        )

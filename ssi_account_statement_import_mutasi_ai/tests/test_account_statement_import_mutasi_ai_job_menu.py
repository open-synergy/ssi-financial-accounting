# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountStatementImportMutasiAiJobMenu(YamlTransactionCase):
    """Field-only scenario tests for the job window action & menuitem."""

    def test_account_statement_import_mutasi_ai_job_menu(self):
        """Run the window action / menuitem data-loading scenarios."""
        self.run_yaml_scenario("test_account_statement_import_mutasi_ai_job_menu.yaml")

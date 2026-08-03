# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountStatementImportMutasiAiJobStatementLink(YamlTransactionCase):
    """Scenario tests for statement linking at job ``create()``."""

    def test_account_statement_import_mutasi_ai_job_statement_link(self):
        """Run the create()-time statement linking scenarios."""
        self.run_yaml_scenario(
            "test_account_statement_import_mutasi_ai_job_statement_link.yaml"
        )

# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountStatementImportMutasiAiJobRetryOk(YamlTransactionCase):
    """Scenario tests for the job ``retry_ok`` compute and ``_retry()``."""

    def test_account_statement_import_mutasi_ai_job_retry_ok(self):
        """Run the ``retry_ok``/``action_retry`` scenarios."""
        self.run_yaml_scenario(
            "test_account_statement_import_mutasi_ai_job_retry_ok.yaml"
        )

# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountStatementImportMutasiAiJobQueueChannel(YamlTransactionCase):
    """Scenario tests for the dedicated ``root.mutasi_ai`` queue channel."""

    def test_account_statement_import_mutasi_ai_job_queue_channel(self):
        """Run the queue channel routing/data scenarios."""
        self.run_yaml_scenario(
            "test_account_statement_import_mutasi_ai_job_queue_channel.yaml"
        )

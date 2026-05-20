# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSsiAccountJournalM2oConfiguratorMixin(TransactionCase):
    def test_mixin_model_exists(self):
        """Verify the mixin abstract model is registered."""
        self.assertIn(
            "mixin.account_journal_m2o_configurator",
            self.env,
            "mixin.account_journal_m2o_configurator should be registered",
        )

    def test_mixin_fields_exist(self):
        """Verify key fields of the mixin are present on the abstract model."""
        model = self.env["mixin.account_journal_m2o_configurator"]
        fields_info = model.fields_get(
            [
                "journal_selection_method",
                "journal_ids",
                "journal_domain",
                "journal_python_code",
            ]
        )
        self.assertIn("journal_selection_method", fields_info)
        self.assertIn("journal_ids", fields_info)
        self.assertIn("journal_domain", fields_info)
        self.assertIn("journal_python_code", fields_info)

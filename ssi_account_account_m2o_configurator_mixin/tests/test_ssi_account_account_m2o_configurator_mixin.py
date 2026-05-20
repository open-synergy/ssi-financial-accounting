# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSsiAccountAccountM2oConfiguratorMixin(TransactionCase):
    def test_mixin_model_exists(self):
        """Verify the mixin abstract model is registered."""
        self.assertIn(
            "mixin.account_account_m2o_configurator",
            self.env,
            "mixin.account_account_m2o_configurator should be registered",
        )

    def test_mixin_fields_exist(self):
        """Verify key fields of the mixin are present on the abstract model."""
        model = self.env["mixin.account_account_m2o_configurator"]
        fields_info = model.fields_get(
            [
                "account_selection_method",
                "account_ids",
                "account_domain",
                "account_python_code",
            ]
        )
        self.assertIn("account_selection_method", fields_info)
        self.assertIn("account_ids", fields_info)
        self.assertIn("account_domain", fields_info)
        self.assertIn("account_python_code", fields_info)

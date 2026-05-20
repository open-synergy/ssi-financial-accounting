# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSsiAccountTypeActive(TransactionCase):
    def test_active_field_default_true(self):
        account_type = self.env["account.account.type"].create(
            {
                "name": "Test Account Type Active",
                "type": "other",
                "internal_group": "equity",
            }
        )
        self.assertTrue(account_type.active)

    def test_deactivate_type_not_in_use_raises_error(self):
        account_type = self.env["account.account.type"].create(
            {
                "name": "Test Account Type Unused",
                "type": "other",
                "internal_group": "equity",
            }
        )
        with self.assertRaises(UserError):
            account_type.write({"active": False})

    def test_check_inactive_returns_false_when_accounts_exist(self):
        account_type = self.env["account.account.type"].search(
            [("internal_group", "=", "equity")], limit=1
        )
        account = self.env["account.account"].search(
            [("user_type_id", "=", account_type.id)], limit=1
        )
        if account:
            self.assertFalse(account_type._check_inactive())

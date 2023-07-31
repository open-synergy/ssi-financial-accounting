# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAccountType(models.Model):
    _name = "account.account.type"
    _inherit = "account.account.type"

    active = fields.Boolean(
        string="Active",
        default=True,
    )

    @api.constrains("active")
    def _constrains_inactive(self):
        for record in self.sudo():
            if not self.active and record._check_inactive():
                error_message = _(
                    """
                Context: Set account type inactive
                Database ID: %s
                Problem: Account type already in used
                Solution: Change account configuration
                """
                    % (record.id)
                )
                raise UserError(error_message)

    def _check_inactive(self):
        result = True
        Account = self.env["account.account"]
        criteria = [("user_type_id", "=", self.id)]
        if Account.search_count(criteria) > 0:
            result = False
        return result

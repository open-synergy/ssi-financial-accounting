# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    direct_cash_flow_type_id = fields.Many2one(
        string="Direct Cash Flow",
        comodel_name="cash_flow_type",
        domain=[
            ("kind", "=", "direct"),
        ],
    )
    indirect_cash_flow_type_id = fields.Many2one(
        string="Indirect Cash Flow",
        comodel_name="cash_flow_type",
        domain=[
            ("kind", "=", "indirect"),
        ],
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="account_type",
    )

    user_type_id = fields.Many2one(
        string="Odoo Type",
    )

    @api.onchange("type_id")
    def onchange_user_type_id(self):
        self.user_type_id = False
        if self.type_id:
            self.user_type_id = self.type_id.odoo_type_id

    @api.onchange("type_id")
    def onchange_reconcile(self):
        self.reconcile = False
        if self.type_id:
            self.reconcile = self.type_id.reconcile

    @api.onchange("type_id")
    def onchange_direct_cash_flow_type_id(self):
        self.direct_cash_flow_type_id = False
        if self.type_id:
            self.direct_cash_flow_type_id = self.type_id.direct_cash_flow_type_id

    @api.onchange("type_id")
    def onchange_indirect_cash_flow_type_id(self):
        self.indirect_cash_flow_type_id = False
        if self.type_id:
            self.indirect_cash_flow_type_id = self.type_id.indirect_cash_flow_type_id

    def _onchange_user_type_id(self):
        return True

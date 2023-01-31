# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


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

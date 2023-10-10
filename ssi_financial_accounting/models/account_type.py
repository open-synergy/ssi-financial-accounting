# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountType(models.Model):
    _name = "account_type"
    _inherit = [
        "mixin.master_data",
    ]
    _description = "Account Type"
    _order = "sequence, name"

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        required=True,
    )
    odoo_type_id = fields.Many2one(
        string="Odoo Internal Type",
        comodel_name="account.account.type",
        required=True,
    )
    reconcile = fields.Boolean(
        string="Reconcile",
        default=False,
    )
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

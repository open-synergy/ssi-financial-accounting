# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CashFlowType(models.Model):
    _name = "cash_flow_type"
    _inherit = [
        "mixin.master_data",
    ]
    _description = "Cash Flow Type"

    kind = fields.Selection(
        string="Direct/Indirect",
        selection=[
            ("direct", "Direct"),
            ("indirect", "Indirect"),
        ],
        required=True,
        default="direct",
    )

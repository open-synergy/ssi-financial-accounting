# Copyright 2022 PT. Simetri Sinergi Indonesia.
# Copyright 2022 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _name = "account.move.line"

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

    @api.model_create_multi
    def create(self, values_list):
        _super = super(AccountMoveLine, self)
        results = _super.create(values_list)
        for result in results:
            direct_cash_flow_type = indirect_cash_flow_type = False
            if (
                result.journal_id.type in ["cash", "bank"]
                and not result.direct_cash_flow_type_id
                and result.account_id.direct_cash_flow_type_id
                and result.account_id.user_type_id.type != "liquidity"
            ):
                direct_cash_flow_type = result.account_id.direct_cash_flow_type_id
            if (
                result.journal_id.type in ["cash", "bank"]
                and not result.direct_cash_flow_type_id
                and result.account_id.direct_cash_flow_type_id
                and result.account_id.user_type_id.type != "liquidity"
            ):
                indirect_cash_flow_type = result.account_id.indirect_cash_flow_type_id

            result.write(
                {
                    "direct_cash_flow_type_id": direct_cash_flow_type
                    and direct_cash_flow_type.id
                    or False,
                    "indirect_cash_flow_type_id": indirect_cash_flow_type
                    and indirect_cash_flow_type.id
                    or False,
                }
            )

        return results

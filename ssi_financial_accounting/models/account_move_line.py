# Copyright 2022 PT. Simetri Sinergi Indonesia.
# Copyright 2022 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


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

    def _transform_to_other_data(self, aml_selector):
        self.ensure_one()
        dict_mappings = safe_eval(aml_selector.field_mapping)
        record = self.read()[0]

        for dict_mapping in dict_mappings.items():
            if dict_mapping[1] == "active_id":
                dict_mappings.update({dict_mapping[0]: aml_selector.active_id})
            else:
                if type(record[dict_mapping[1]]) is tuple:
                    data = record[dict_mapping[1]][0]
                else:
                    data = record[dict_mapping[1]]
                dict_mappings.update(
                    {
                        dict_mapping[0]: data,
                    }
                )
        self.env[aml_selector.active_model].create(dict_mappings)

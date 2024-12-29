# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountBankStatementLine(models.Model):
    _name = "account.bank.statement.line"
    _inherit = [
        "account.bank.statement.line",
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("statement_id", False):
                bs = self.env["account.bank.statement"].browse(vals["statement_id"])
                if bs.operating_unit_id:
                    vals["operating_unit_id"] = bs.operating_unit_id.id
        return super().create(vals_list)

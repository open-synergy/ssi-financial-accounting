# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _name = "account.bank.statement"
    _inherit = [
        "account.bank.statement",
        "mixin.sequence",
    ]

    name = fields.Char(
        default='/',
    )

    def button_post(self):
        # hanya implement sequence di transaksi yang name nya tidak diinput manual oleh user
        for rec in self.filtered(lambda s: not s.name or s.name == '/'):
            if not rec.name:
                rec.write({'name': '/'})
            rec._create_sequence()
        res = super(AccountBankStatement, self).button_post()
        for rec in self:
            if not rec.line_ids:
                rec.button_validate()
        return res

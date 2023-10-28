# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def button_post(self):
        res = super(AccountBankStatement, self).button_post()
        for rec in self:
            if not rec.line_ids:
                rec.button_validate()
        return res

# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountBankStatement(models.Model):
    _name = "account.bank.statement"
    _inherit = [
        "account.bank.statement",
        "mixin.single_operating_unit",
    ]

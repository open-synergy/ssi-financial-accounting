# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountJournal(models.Model):
    _name = "account.journal"
    _inherit = [
        "account.journal",
        "mixin.multiple_operating_unit",
    ]

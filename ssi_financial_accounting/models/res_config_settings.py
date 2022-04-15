# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _name = "res.config.settings"
    _inherit = [
        "res.config.settings",
        "abstract.config.settings",
    ]

    module_ssi_voucher_bank_cash = fields.Boolean(
        string="Bank & Cash Voucher",
    )
    module_ssi_voucher_cheque = fields.Boolean(
        string="Cheque Voucher",
    )
    module_ssi_voucher_giro = fields.Boolean(
        string="Giro Voucher",
    )
    module_ssi_voucher_advance_settlement = fields.Boolean(
        string="Advance Settlement Voucher",
    )
    module_ssi_voucher_refund_settlement = fields.Boolean(
        string="Refund Settlement Voucher",
    )
    module_ssi_voucher_invoice_settlement = fields.Boolean(
        string="Invoice Settlement Voucher",
    )

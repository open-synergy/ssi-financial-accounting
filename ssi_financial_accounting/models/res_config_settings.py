# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    module_ssi_fixed_asset = fields.Boolean(
        string="Fixed Asset",
    )
    module_ssi_fixed_asset_disposal = fields.Boolean(
        string="Fixed Asset Disposal",
    )
    module_ssi_fixed_asset_improvement = fields.Boolean(
        string="Fixed Asset Improvement",
    )
    module_ssi_fixed_asset_estimation_change = fields.Boolean(
        string="Fixed Asset Estimation Change",
    )
    module_ssi_fixed_asset_complex = fields.Boolean(
        string="Complex Fixed Asset",
    )
    module_ssi_fixed_asset_in_progress = fields.Boolean(
        string="Fixed Asset in Progress",
    )
    module_ssi_account_amortization = fields.Boolean(
        string="Prepaid Expense & Deferred Revenue Amortization",
    )
    module_ssi_account_currency_revaluation = fields.Boolean(
        string="Currency Revaluation",
    )

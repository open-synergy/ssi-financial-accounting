# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _name = "account.bank.statement"
    _inherit = [
        "account.bank.statement",
        "mixin.sequence",
        "mixin.policy",
    ]

    def _compute_policy(self):
        _super = super()
        _super._compute_policy()

    name = fields.Char(
        default="/",
    )
    post_ok = fields.Boolean(
        string="Can Post",
        compute="_compute_policy",
        compute_sudo=True,
        default=False,
    )
    validate_ok = fields.Boolean(
        string="Can Validate",
        compute="_compute_policy",
        compute_sudo=True,
        default=False,
    )
    reopen_ok = fields.Boolean(
        string="Can Reset to New",
        compute="_compute_policy",
        compute_sudo=True,
        default=False,
    )
    reprocess_ok = fields.Boolean(
        string="Can Reset to Processing",
        compute="_compute_policy",
        compute_sudo=True,
        default=False,
    )
    cash_box_ok = fields.Boolean(
        string="Can Take Money In/Out",
        compute="_compute_policy",
        compute_sudo=True,
        default=False,
    )

    def button_post(self):
        # hanya implement sequence di transaksi yang name nya tidak diinput manual oleh user
        for rec in self.filtered(lambda s: not s.name or s.name == "/"):
            if not rec.name:
                rec.write({"name": "/"})
            rec._create_sequence()
        res = super().button_post()
        for rec in self:
            if not rec.line_ids:
                rec.button_validate()
        return res

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "post_ok",
            "validate_ok",
            "reopen_ok",
            "reprocess_ok",
            "cash_box_ok",
        ]
        res += policy_field
        return res

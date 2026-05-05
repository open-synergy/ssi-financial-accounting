# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountBankStatement(models.Model):
    _name = "account.bank.statement"
    _inherit = [
        "account.bank.statement",
        "mixin.sequence",
        "mixin.policy",
        "mixin.print_document",
    ]
    _automatically_insert_print_button = True

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
            rec._create_sequence()  # pylint: disable=protected-access
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

    def check_group(self, journal_type):
        user = self.env.user
        if journal_type == "bank" and user.has_group(
            "ssi_financial_accounting.bank_statement_user_group"
        ):
            return True
        if journal_type == "cash" and user.has_group(
            "ssi_financial_accounting.cash_register_user_group"
        ):
            return True

        return False

    @api.model
    def create(self, vals):
        journal_type = vals.get("journal_type") or self.env.context.get(
            "journal_type", False
        )
        if journal_type and not self.check_group(journal_type):
            raise UserError(_("You do not have access to this record."))
        return super().create(vals)

    def write(self, vals):
        for record in self:
            if not record.check_group(record.journal_type):
                raise UserError(_("You do not have access to this record."))
        return super().write(vals)

    def unlink(self):
        for record in self:
            if not record.check_group(record.journal_type):
                raise UserError(_("You do not have access to this record."))
        return super().unlink()

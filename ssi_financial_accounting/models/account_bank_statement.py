# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import api, fields, models


class AccountBankStatement(models.Model):  # pylint: disable=too-few-public-methods
    _name = "account.bank.statement"
    _inherit = [
        "account.bank.statement",
        "mixin.sequence",
        "mixin.policy",
        "mixin.print_document",
    ]
    _automatically_insert_print_button = True

    def _compute_policy(self):  # pylint: disable=missing-return
        _super = super()
        _super._compute_policy()  # pylint: disable=protected-access

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
    def fields_view_get(  # pylint: disable=deprecated-odoo-model-method
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        _super = super()
        result = _super.fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type not in ("tree", "form"):
            return result

        ctx = self.env.context
        journal_type = ctx.get("journal_type")
        if not journal_type:
            return result

        can_ced = False

        if self.check_group(journal_type):
            can_ced = True

        if can_ced:
            doc = etree.XML(result["arch"])
            doc.set("create", "true")
            doc.set("edit", "true")
            doc.set("delete", "true")
            result["arch"] = etree.tostring(doc, encoding="unicode")

        return result

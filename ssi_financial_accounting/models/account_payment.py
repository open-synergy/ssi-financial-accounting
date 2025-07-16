# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = [
        "account.payment",
        "mixin.print_document",
        "mixin.policy",
    ]

    _automatically_insert_print_button = True

    def _compute_policy(self):
        _super = super()
        _super._compute_policy()

    # INVOICE
    confirm_ok = fields.Boolean(
        string="Can Confirm",
        compute="_compute_policy",
        default=False,
    )
    mark_as_sent_ok = fields.Boolean(
        string="Can Mark as Sent",
        compute="_compute_policy",
        default=False,
    )
    unmark_as_sent_ok = fields.Boolean(
        string="Can Unmark as Sent",
        compute="_compute_policy",
        default=False,
    )
    cancel_ok = fields.Boolean(
        string="Can Cancel",
        compute="_compute_policy",
        default=False,
    )
    restart_ok = fields.Boolean(
        string="Can Reset To Draft",
        compute="_compute_policy",
        default=False,
    )

    @api.onchange(
        "payment_type",
    )
    def onchange_policy_template_id(self):
        template_id = self._get_template_policy()
        self.policy_template_id = template_id

    @api.model
    def _get_policy_field(self):
        res = super()._get_policy_field()
        policy_field = [
            "mark_as_sent_ok",
            "confirm_ok",
            "unmark_as_sent_ok",
            "cancel_ok",
            "restart_ok",
        ]
        res += policy_field
        return res

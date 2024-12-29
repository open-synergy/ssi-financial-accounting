# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = [
        "account.move",
        "mixin.single_operating_unit",
    ]

    @api.onchange("invoice_line_ids")
    def _onchange_invoice_line_ids(self):
        res = super()._onchange_invoice_line_ids()
        if self.operating_unit_id:
            for line in self.line_ids:
                line.operating_unit_id = self.operating_unit_id
        return res

    @api.onchange("operating_unit_id")
    def _onchange_operating_unit(self):
        if self.operating_unit_id and (
            not self.journal_id
            or self.journal_id.operating_unit_ids.id not in [self.operating_unit_id]
        ):
            journal = self.env["account.journal"].search(
                [("type", "=", self.journal_id.type)]
            )
            jf = journal.filtered(
                lambda aj: aj.operating_unit_ids.id in [self.operating_unit_id]
            )
            if not jf:
                self.journal_id = journal[0]
            else:
                self.journal_id = jf[0]
            for line in self.line_ids:
                line.operating_unit_id = self.operating_unit_id

    @api.onchange("journal_id")
    def _onchange_journal(self):
        if (
            self.journal_id
            and self.journal_id.operating_unit_ids
            and self.journal_id.operating_unit_ids.id not in [self.operating_unit_id.id]
        ):
            self.operating_unit_id = self.journal_id.operating_unit_ids[0]
            for line in self.line_ids:
                line.operating_unit_id = self.journal_id.operating_unit_id

    @api.constrains("operating_unit_id", "journal_id")
    def _check_journal_operating_unit(self):
        for move in self:
            if (
                move.journal_id.operating_unit_ids
                and move.operating_unit_id
                and move.operating_unit_id.id
                not in [move.journal_id.operating_unit_id.id]
            ):
                # Change journal_id if create move from other model. e.g., sale.order
                if (
                    move._context.get("active_model")
                    and move._context.get("active_model") != "account.move"
                ):
                    move._onchange_operating_unit()
                    if (
                        move.journal_id.operating_unit_ids
                        and move.operating_unit_id
                        and move.operating_unit_id.id
                        not in move.journal_id.operating_unit_ids.ids
                    ):
                        raise UserError(
                            _("The OU in the Move and in Journal must be the same.")
                        )
                else:
                    raise UserError(
                        _("The OU in the Move and in Journal must be the same.")
                    )
        return True

    @api.constrains("operating_unit_id", "company_id")
    def _check_company_operating_unit(self):
        for move in self:
            if (
                move.company_id
                and move.operating_unit_id
                and move.company_id != move.operating_unit_id.company_id
            ):
                raise UserError(
                    _(
                        "The Company in the Move and in "
                        "Operating Unit must be the same."
                    )
                )
        return True

# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = [
        "account.move.line",
        "mixin.single_operating_unit",
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("move_id", False):
                move = self.env["account.move"].browse(vals["move_id"])
                if move.operating_unit_id:
                    vals["operating_unit_id"] = move.operating_unit_id.id
        return super().create(vals_list)

    @api.model
    def _query_get(self, domain=None):
        if domain is None:
            domain = []
        if self._context.get("operating_unit_ids", False):
            domain.append(
                ("operating_unit_id", "in", self._context.get("operating_unit_ids"))
            )
        return super()._query_get(domain)

    @api.constrains("operating_unit_id", "company_id")
    def _check_company_operating_unit(self):
        for rec in self:
            if (
                rec.company_id
                and rec.operating_unit_id
                and rec.company_id != rec.operating_unit_id.company_id
            ):
                raise UserError(
                    _(
                        "Configuration error. The Company in the"
                        " Move Line and in the Operating Unit must "
                        "be the same."
                    )
                )

    @api.constrains("operating_unit_id", "move_id")
    def _check_move_operating_unit(self):
        for rec in self:
            if (
                rec.move_id
                and rec.move_id.operating_unit_id
                and rec.operating_unit_id
                and rec.move_id.operating_unit_id != rec.operating_unit_id
            ):
                raise UserError(
                    _(
                        "Configuration error. The Operating Unit in"
                        " the Move Line and in the Move must be the"
                        " same."
                    )
                )

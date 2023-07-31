# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "move_type",
        "line_ids.amount_residual",
    )
    def _compute_move_line_payment_ids(self):
        for document in self:
            result = []
            json_values = document._get_reconciled_info_JSON_values()
            if json_values:
                for values in json_values:
                    result.append(values["payment_id"])
            document.move_line_payment_ids = [(6, 0, result)]

    move_line_payment_ids = fields.Many2many(
        string="Payments",
        comodel_name="account.move.line",
        compute="_compute_move_line_payment_ids",
        store=True,
    )

    @api.depends(
        "move_line_payment_ids",
        "move_line_payment_ids.date",
    )
    def _compute_last_payment_date(self):
        for document in self:
            last_payment_date = last_payment_line_id = False
            if document.move_line_payment_ids:
                payment = document.move_line_payment_ids.sorted(
                    key=lambda r: r.date, reverse=True
                )[0]
                last_payment_date = payment.date
                last_payment_line_id = payment.id
            document.last_payment_date = last_payment_date
            document.last_payment_line_id = last_payment_line_id

    last_payment_date = fields.Date(
        string="Last Payment Date",
        compute="_compute_last_payment_date",
        store=True,
        readonly=True,
    )
    last_payment_line_id = fields.Many2one(
        string="#Last Payment Line",
        comodel_name="account.move.line",
        compute="_compute_last_payment_date",
        store=True,
        readonly=True,
    )

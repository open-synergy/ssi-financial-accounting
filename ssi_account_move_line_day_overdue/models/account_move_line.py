# Copyright 2022 PT. Simetri Sinergi Indonesia.
# Copyright 2022 OpenSynergy Indonesia
# License lgpl-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
try:
    pass
except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _name = "account.move.line"

    days_overdue = fields.Integer(
        string="Days Overdue",
    )

    @api.model
    def compute_days_overdue(self):
        obj_ml = self.env["account.move.line"]
        criteria = [
            ("account_id.reconcile", "=", True),
            ("reconciled", "=", False),
        ]
        move_lines = obj_ml.search(criteria)
        for move_line in move_lines:
            move_line._compute_days_overdue()

    def _compute_days_overdue(self):
        self.ensure_one()
        day_diff = 0
        if self.date_maturity:
            dt_date_due = fields.Datetime.to_datetime(self.date_maturity)
            dt_date_today = fields.Datetime.now()
            day_diff = (dt_date_today - dt_date_due).days
        self.write({"days_overdue": day_diff})

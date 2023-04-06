import operator
from datetime import date, datetime, timedelta

from odoo import api, models
from odoo.tools import float_is_zero


class AgedPartnerBalanceReport(models.AbstractModel):
    _inherit = 'report.account_financial_report.aged_partner_balance'

    @api.model
    def _calculate_amounts(
        self, ag_pb_data, acc_id, prt_id, residual, due_date, date_at_object
    ):
        if self._context.get('active_model') == 'aged.partner.balance.report.wizard':
            wizard_id = self.env['aged.partner.balance.report.wizard'].browse(self._context['active_id'])
            ag_pb_data[acc_id]["residual"] += residual
            ag_pb_data[acc_id][prt_id]["residual"] += residual
            today = date_at_object
            if not due_date or today <= due_date:
                ag_pb_data[acc_id]["current"] += residual
                ag_pb_data[acc_id][prt_id]["current"] += residual
            elif today <= due_date + timedelta(days=wizard_id.get_interval(1)):
                ag_pb_data[acc_id]["30_days"] += residual
                ag_pb_data[acc_id][prt_id]["30_days"] += residual
            elif today <= due_date + timedelta(days=wizard_id.get_interval(2)):
                ag_pb_data[acc_id]["60_days"] += residual
                ag_pb_data[acc_id][prt_id]["60_days"] += residual
            elif today <= due_date + timedelta(days=wizard_id.get_interval(3)):
                ag_pb_data[acc_id]["90_days"] += residual
                ag_pb_data[acc_id][prt_id]["90_days"] += residual
            elif today <= due_date + timedelta(days=wizard_id.get_interval(4)):
                ag_pb_data[acc_id]["120_days"] += residual
                ag_pb_data[acc_id][prt_id]["120_days"] += residual
            else:
                ag_pb_data[acc_id]["older"] += residual
                ag_pb_data[acc_id][prt_id]["older"] += residual
            return ag_pb_data
        else:
            return super(AgedPartnerBalanceReport, self)._calculate_amounts(ag_pb_data, acc_id, prt_id, residual, due_date, date_at_object)

    @api.model
    def _compute_maturity_date(self, ml, date_at_object):
        if self._context.get('active_model') == 'aged.partner.balance.report.wizard':
            wizard_id = self.env['aged.partner.balance.report.wizard'].browse(self._context['active_id'])
            ml.update(
                {
                    "current": 0.0,
                    "30_days": 0.0,
                    "60_days": 0.0,
                    "90_days": 0.0,
                    "120_days": 0.0,
                    "older": 0.0,
                }
            )
            due_date = ml["due_date"]
            amount = ml["residual"]
            today = date_at_object
            if not due_date or today <= due_date:
                ml["current"] += amount
            elif today <= due_date + timedelta(days=wizard_id.get_interval(1)):
                ml["30_days"] += amount
            elif today <= due_date + timedelta(days=wizard_id.get_interval(2)):
                ml["60_days"] += amount
            elif today <= due_date + timedelta(days=wizard_id.get_interval(3)):
                ml["90_days"] += amount
            elif today <= due_date + timedelta(days=wizard_id.get_interval(4)):
                ml["120_days"] += amount
            else:
                ml["older"] += amount
        else:
            return super(AgedPartnerBalanceReport, self)._compute_maturity_date(ml, date_at_object)

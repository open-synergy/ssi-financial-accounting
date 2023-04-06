from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AgedPartnerBalanceReportWizard(models.TransientModel):
    _inherit = 'aged.partner.balance.report.wizard'

    use_auto_interval = fields.Boolean(
        string='Automatic Interval',
        default=True)
    due_interval = fields.Integer(
        string='Due Interval',
        required=False,
        default=30)
    interval_1 = fields.Integer(
        string='Interval I',
        required=False)
    interval_2 = fields.Integer(
        string='Interval II',
        required=False)
    interval_3 = fields.Integer(
        string='Interval III',
        required=False)
    interval_4 = fields.Integer(
        string='Interval IV',
        required=False)

    @api.constrains('due_interval')
    def validate_due_interval(self):
        for rec in self:
            if rec.due_interval < 1:
                raise ValidationError(_('Due interval must be greather than zero.'))

    def get_interval_label(self):
        if self.use_auto_interval:
            interval_labels = {}
            for x in range(5):
                if x < 4:
                    label = f'{(x * self.due_interval + 1)} - {((x + 1) * self.due_interval)} d.'
                else:
                    label = f'> {(x * self.due_interval)} d.'
                interval_labels[x] = label
        else:
            interval_labels = {
                0: f'1 - {self.interval_1} d.',
                1: f'{(self.interval_1 + 1)} - {self.interval_2} d.',
                2: f'{(self.interval_2 + 1)} - {self.interval_3} d.',
                3: f'{(self.interval_3 + 1)} - {self.interval_4} d.',
                4: f'> {self.interval_4} d.',
            }
        return {
            'due_interval': self.due_interval,
            'interval_label1': interval_labels[0],
            'interval_label2': interval_labels[1],
            'interval_label3': interval_labels[2],
            'interval_label4': interval_labels[3],
            'interval_label5': interval_labels[4],
        }

    def _prepare_report_aged_partner_balance(self):
        res = super(AgedPartnerBalanceReportWizard, self)._prepare_report_aged_partner_balance()
        interval_labels = self.get_interval_label()
        res.update({
            'due_interval': self.due_interval,
            'interval_label1': interval_labels['interval_label1'],
            'interval_label2': interval_labels['interval_label2'],
            'interval_label3': interval_labels['interval_label3'],
            'interval_label4': interval_labels['interval_label4'],
            'interval_label5': interval_labels['interval_label5'],
        })
        return res

    def get_interval(self, index):
        self.ensure_one()
        if self.use_auto_interval:
            interval = self.due_interval * index
        else:
            interval = getattr(self, f'interval_{index}')
        return interval

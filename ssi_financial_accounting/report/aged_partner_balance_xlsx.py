from odoo import _, models


class AgedPartnerBalanceXslx(models.AbstractModel):
    _inherit = 'report.a_f_r.report_aged_partner_balance_xlsx'

    def _get_report_columns(self, report):
        report_columns = super(AgedPartnerBalanceXslx, self)._get_report_columns(report=report)
        interval_labels = report.get_interval_label()
        if not report.show_move_line_details:
            indexs = [3, 4, 5, 6, 7, 8]
        else:
            indexs = [9, 10, 11, 12, 13, 14]
        report_columns[indexs[0]]['header'] = interval_labels['interval_label1']
        report_columns[indexs[1]]['header'] = interval_labels['interval_label2']
        report_columns[indexs[2]]['header'] = interval_labels['interval_label3']
        report_columns[indexs[3]]['header'] = interval_labels['interval_label4']
        report_columns[indexs[4]]['header'] = interval_labels['interval_label5']
        return report_columns

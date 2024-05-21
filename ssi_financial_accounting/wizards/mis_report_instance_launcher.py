# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MisReportInstanceLauncher(models.TransientModel):
    _name = "mis_report_instance_launcher"
    _description = "Mis Report Instance Launcher"

    base_date = fields.Date(
        string="Base Date",
        required=True
    )
    mis_report_instance_id = fields.Many2one(
        comodel_name="mis.report.instance",
        string="MIS Report",
        required=True
    )

    def action_open_report(self):
        self.mis_report_instance_id.write({"date": self.base_date})
        return self.mis_report_instance_id.preview()

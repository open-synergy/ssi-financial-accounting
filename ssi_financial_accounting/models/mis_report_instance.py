# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    parent_menu_id = fields.Many2one(
        comodel_name="ir.ui.menu",
        domain=[("action", "=", False)],
        string="Parent Menu"
    )
    window_action_id = fields.Many2one(
        comodel_name="ir.actions.act_window",
        string="Action",
        copy=False,
        readonly=True
    )
    menu_id = fields.Many2one(
        comodel_name="ir.ui.menu",
        string="Menu",
        copy=False,
        readonly=True
    )

    def action_create_menu(self):
        for rec in self:
            window_action_id = self.env["ir.actions.act_window"].sudo().create({
                "name": rec.name,
                "res_model": "mis_report_instance_launcher",
                "target": "new",
                "view_mode": "form",
                "view_id": self.env.ref("ssi_financial_accounting.mis_report_instance_launcher_form_view").sudo().id,
                "context": "{'default_mis_report_instance_id':%d}" % rec.id,
            })
            menu_id = self.env['ir.ui.menu'].sudo().create({
                "name": rec.name,
                "action": "ir.actions.act_window,%d" % (window_action_id.id,),
                "parent_id": rec.parent_menu_id.id,
            })
            rec.write({
                "window_action_id": window_action_id.id,
                "menu_id": menu_id.id,
            })

    def action_delete_menu(self):
        for rec in self:
            rec.window_action_id.sudo().unlink()
            rec.menu_id.sudo().unlink()

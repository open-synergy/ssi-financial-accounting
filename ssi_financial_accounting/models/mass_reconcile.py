# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMassReconcileMethod(models.Model):
    _inherit = "account.mass.reconcile.method"

    filter_partner = fields.Boolean(
        string="Filter Partner",
        help="If checked, only move lines belonging to partners matching "
        "the Partner Domain will be considered for reconciliation.",
    )
    partner_domain = fields.Text(
        string="Partner Domain",
        help="Domain expression to filter partners for reconciliation. "
        "Only move lines belonging to partners matching this domain "
        "will be considered during the Advanced Partner Only reconciliation method.",
    )

    def _selection_name(self):
        methods = super()._selection_name()
        methods += [
            (
                "mass.reconcile.advanced.partner",
                "Advanced. Partner Only (Partial)",
            ),
        ]
        return methods


class AccountMassReconcile(models.Model):
    _inherit = "account.mass.reconcile"

    def _prepare_run_transient(self, rec_method):
        vals = super()._prepare_run_transient(rec_method)
        vals["filter_partner"] = rec_method.filter_partner
        vals["partner_domain"] = rec_method.partner_domain
        return vals

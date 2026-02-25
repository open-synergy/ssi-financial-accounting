# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMassReconcileMethod(models.Model):
    _inherit = "account.mass.reconcile.method"

    def _selection_name(self):
        methods = super()._selection_name()
        methods += [
            (
                "mass.reconcile.advanced.partner",
                "Advanced. Partner Only (Partial)",
            ),
        ]
        return methods

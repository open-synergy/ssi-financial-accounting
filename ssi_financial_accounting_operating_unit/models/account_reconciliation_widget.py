# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class AccountReconciliationWidget(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _domain_move_lines_for_reconciliation(
        self,
        st_line,
        aml_accounts,
        partner_id,
        excluded_ids=None,
        search_str=False,
        mode="rp",
    ):
        domain = super()._domain_move_lines_for_reconciliation(
            st_line,
            aml_accounts,
            partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            mode=mode,
        )
        # Superuser bypasses record rules; mirror that here so the widget
        # behaves consistently with account_move_line_rule_ou, which is only
        # applied by the ORM on search()/read() and not on the raw SQL this
        # widget builds via _where_calc().
        if self.env.su:
            return domain
        operating_unit_ids = self.env.user.operating_unit_ids.ids
        return expression.AND(
            [
                domain,
                [
                    "|",
                    ("operating_unit_id", "=", False),
                    ("operating_unit_id", "in", operating_unit_ids),
                ],
            ]
        )

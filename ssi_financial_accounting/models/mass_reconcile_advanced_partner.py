# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MassReconcileAdvancedPartner(models.TransientModel):
    """Advanced reconciliation method that matches only by partner.

    This method:
    - Matches move lines only by partner_id
    - Allows partial reconciliation
    - Allows reconciliation with multiple lines (N debits vs M credits)
    """

    _name = "mass.reconcile.advanced.partner"
    _inherit = "mass.reconcile.advanced"
    _description = "Advanced. Partner Only (Partial)"

    filter_partner = fields.Boolean(
        string="Filter Partner",
        help="If checked, only move lines belonging to partners matching "
        "the Partner Domain will be considered for reconciliation.",
    )
    partner_domain = fields.Text(
        string="Partner Domain",
        help="Domain expression to filter partners for reconciliation. "
        "Only move lines belonging to partners matching this domain "
        "will be considered for reconciliation.",
    )

    def _where_query(self, *args, **kwargs):
        where, params = super()._where_query(*args, **kwargs)
        if self.filter_partner and self.partner_domain:
            domain = safe_eval(self.partner_domain)
            partner_ids = self.env["res.partner"].search(domain).ids
            if partner_ids:
                where += " AND account_move_line.partner_id IN %s"
                params.append(tuple(partner_ids))
            else:
                where += " AND 1=0"
        return where, params

    @staticmethod
    def _skip_line(move_line):
        """Skip lines without a partner."""
        return not move_line.get("partner_id")

    @staticmethod
    def _matchers(move_line):
        """Match only by partner_id."""
        return (("partner_id", move_line["partner_id"]),)

    @staticmethod
    def _opposite_matchers(move_line):
        """Yield only partner_id as opposite matcher."""
        yield ("partner_id", move_line["partner_id"])

    @staticmethod
    def _group_lines_sort_key(move_line):
        """Sort key applied to a reconcile group's lines before reconciling.

        `reconcile_group_ids` is a Python `set`, so iterating it yields an
        arbitrary order unrelated to invoice date or number. Odoo core's
        `account.move.line.reconcile()` preserves whatever order it is
        given (it filters the recordset into debit/credit sub-lists
        without re-sorting), so sorting here by date (oldest first) is
        what makes an available credit apply against the oldest open
        invoice first (FIFO) instead of whichever invoice happened to
        land first in the unordered set.
        """
        return (move_line["date"], move_line["id"])

    def _rec_group(self, reconcile_groups, lines_by_id):
        """Override to also track partially reconciled lines.

        The base implementation only tracks fully reconciled lines.
        This version also includes partial reconciliations, and sorts
        each group's lines oldest-first (see `_group_lines_sort_key`)
        before reconciling so partial payments settle the oldest open
        invoice of the partner first.
        """
        reconciled_ids = []
        for group_count, reconcile_group_ids in enumerate(reconcile_groups, start=1):
            _logger.debug(
                "Reconciling group %d/%d with ids %s",
                group_count,
                len(reconcile_groups),
                reconcile_group_ids,
            )
            group_lines = sorted(
                (lines_by_id[lid] for lid in reconcile_group_ids),
                key=self._group_lines_sort_key,
            )
            reconciled, full = self._reconcile_lines(group_lines, allow_partial=True)
            if reconciled:
                reconciled_ids += reconcile_group_ids
        return reconciled_ids

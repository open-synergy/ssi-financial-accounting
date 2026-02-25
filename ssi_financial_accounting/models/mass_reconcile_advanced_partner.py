# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

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

    def _rec_group(self, reconcile_groups, lines_by_id):
        """Override to also track partially reconciled lines.

        The base implementation only tracks fully reconciled lines.
        This version also includes partial reconciliations.
        """
        reconciled_ids = []
        for group_count, reconcile_group_ids in enumerate(reconcile_groups, start=1):
            _logger.debug(
                "Reconciling group %d/%d with ids %s",
                group_count,
                len(reconcile_groups),
                reconcile_group_ids,
            )
            group_lines = [lines_by_id[lid] for lid in reconcile_group_ids]
            reconciled, full = self._reconcile_lines(group_lines, allow_partial=True)
            if reconciled:
                reconciled_ids += reconcile_group_ids
        return reconciled_ids

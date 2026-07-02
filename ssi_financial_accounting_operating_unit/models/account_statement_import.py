# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        stmts_vals = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        ous = journal.operating_unit_ids
        for st_vals in stmts_vals:
            if st_vals.get("operating_unit_id"):
                continue
            if len(ous) == 1:
                st_vals["operating_unit_id"] = ous.id
            elif len(ous) > 1:
                default_ou = self.env["res.users"].operating_unit_default_get()
                st_vals["operating_unit_id"] = (
                    default_ou.id if default_ou in ous else ous[0].id
                )
            # journal without OU: leave default (no mismatch possible)
        return stmts_vals

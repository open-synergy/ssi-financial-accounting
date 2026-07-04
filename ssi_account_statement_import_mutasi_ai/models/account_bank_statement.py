# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    mutasi_ai_job_ids = fields.Many2many(
        string="Mutasi AI Import Jobs",
        comodel_name="account.statement.import.mutasi.ai.job",
        relation="account_statement_import_mutasi_ai_job_statement_rel",
        column1="statement_id",
        column2="job_id",
        readonly=True,
        help="Mutasi AI extraction job(s) whose imported transactions "
        "landed on this bank statement. Read-only; jobs are created and "
        "processed from the bank statement import wizard.",
    )

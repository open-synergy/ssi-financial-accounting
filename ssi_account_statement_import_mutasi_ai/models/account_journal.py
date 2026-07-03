# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    default_mutasi_ai_backend_id = fields.Many2one(
        string="Default Mutasi AI Backend",
        comodel_name="account.statement.import.mutasi.ai.backend",
        help=(
            "Default mutasi-ai backend pre-selected when importing bank "
            "statements via this journal. Users can still override it "
            "per-import in the Import Statement wizard."
        ),
    )

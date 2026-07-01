# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    default_pdf_mapping_id = fields.Many2one(
        string="Default PDF Statement Mapping",
        comodel_name="account.statement.import.pdf.mapping",
        help=(
            "Default PDF mapping pre-selected when importing bank statements from PDF "
            "files via this journal. Users can still override it per-import in the "
            "Import Statement wizard."
        ),
    )

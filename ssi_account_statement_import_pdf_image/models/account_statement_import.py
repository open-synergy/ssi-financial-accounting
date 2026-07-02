# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    pdf_image_mapping_id = fields.Many2one(
        string="PDF Image Statement Mapping",
        comodel_name="account.statement.import.pdf.image.mapping",
        help=(
            "Select the PDF image (OCR) mapping configuration to use when "
            "importing a scanned PDF bank statement. If set and the uploaded "
            "file ends with '.pdf', the mapping's parser_code will be executed "
            "against OCR-extracted text to extract transactions. "
            "Leave empty to use other installed format parsers."
        ),
    )

    def _parse_file(self, data_file):
        self.ensure_one()
        filename = self.statement_filename or ""
        if self.pdf_image_mapping_id and filename.lower().endswith(".pdf"):
            return self.pdf_image_mapping_id.parse(data_file, filename)
        return super()._parse_file(data_file)

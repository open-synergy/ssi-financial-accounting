# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "SSI PDF Statement Import",
    "version": "14.0.1.0.0",
    "summary": "Import bank statements from PDF files using configurable Python parsers",
    "category": "Accounting",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "website": "https://simetri-sinergi.id",
    "license": "AGPL-3",
    "depends": [
        "ssi_account_statement_import",
    ],
    "external_dependencies": {
        "python": ["pdfplumber"],
    },
    "data": [
        "security/res_groups/account_statement_import_pdf_mapping.xml",
        "security/ir_model_access/account_statement_import_pdf_mapping.xml",
        "views/account_statement_import_pdf_mapping_views.xml",
        "views/account_statement_import_views.xml",
        "views/account_journal_views.xml",
    ],
    "installable": True,
    "application": False,
}

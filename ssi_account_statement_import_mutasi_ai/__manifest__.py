# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "SSI Mutasi AI Statement Import",
    "version": "14.0.1.3.1",
    "summary": "Import bank statements using the mutasi-ai AI extraction service, "
    "processed asynchronously via queue_job",
    "category": "Accounting",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "contributors": [
        "Andhitia Rama <andhitia.r@gmail.com>",
    ],
    "website": "https://simetri-sinergi.id",
    "license": "AGPL-3",
    "depends": [
        "ssi_account_statement_import",
        "queue_job",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "security/res_groups/account_statement_import_mutasi_ai_backend.xml",
        "security/ir_model_access/account_statement_import_mutasi_ai_backend.xml",
        "security/ir_model_access/account_statement_import_mutasi_ai_job.xml",
        "data/ir_sequence.xml",
        "views/account_statement_import_mutasi_ai_backend_views.xml",
        "views/account_statement_import_mutasi_ai_job_views.xml",
        "views/account_statement_import_views.xml",
        "views/account_journal_views.xml",
        "views/account_bank_statement_views.xml",
    ],
    "installable": True,
    "application": False,
}

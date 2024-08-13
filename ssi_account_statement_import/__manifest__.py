# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Add Wizard to Import Statement",
    "version": "14.0.1.1.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "ssi_financial_accounting",
        "account_statement_import",
        "account_reconciliation_widget",
    ],
    "data": [
        "views/account_bank_statement_views.xml",
    ],
    "demo": [],
    "qweb": [
        "static/src/xml/account_reconciliation.xml",
    ],
}

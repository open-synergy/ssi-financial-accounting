# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Add Wizard to Import Statement",
    "version": "14.0.1.0.0",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia,OpenSynergy Indonesia",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "ssi_financial_accounting",
        "account_statement_import",
    ],
    "data": [
        "views/account_bank_statement_views.xml",
    ],
    "demo": [],
}
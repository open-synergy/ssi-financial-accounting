# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Add Wizard to Create Liquidity Journal",
    "version": "14.0.1.0.1",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia,OpenSynergy Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/wizard_create_liquidity_journal.xml",
    ],
    "demo": [],
}

# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Sequence Mixin Implementation on Journal Entry",
    "version": "14.0.1.2.0",
    "website": "https://simetri-sinergi.id",
    "author": "PT. Simetri Sinergi Indonesia,OpenSynergy Indonesia",
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "account",
        "ssi_sequence_mixin",
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "data/sequence_template_data.xml",
        "views/account_journal_views.xml",
    ],
    "demo": [],
}

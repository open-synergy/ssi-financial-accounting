# Copyright 2022 PT. Simetri Sinergi Indonesia.
# Copyright 2022 OpenSynergy Indonesia
# License lgpl-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Move Line Days Overdue",
    "version": "14.0.1.0.3",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_financial_accounting",
    ],
    "data": [
        "data/ir_cron_data.xml",
        "views/account_move_line_views.xml",
    ],
}

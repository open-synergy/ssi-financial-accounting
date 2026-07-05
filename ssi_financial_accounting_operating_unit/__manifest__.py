# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Financial Accounting + Operating Unit",
    "version": "14.0.1.3.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_financial_accounting",
        "ssi_operating_unit_mixin",
        "account_statement_import",
    ],
    "data": [
        "security/res_group/journal_entry.xml",
        "security/res_group/bank_statement.xml",
        "security/res_group/account_payment.xml",
        "security/ir_rule/account_journal.xml",
        "security/ir_rule/account_move.xml",
        "security/ir_rule/account_move_line.xml",
        "security/ir_rule/account_bank_statement.xml",
        "security/ir_rule/account_payment.xml",
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
        "views/account_move_line_views.xml",
        "views/account_bank_statement_views.xml",
        "views/account_payment_views.xml",
    ],
    "demo": [],
}

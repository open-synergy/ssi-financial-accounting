# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Financial Accounting",
    "version": "14.0.3.0.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "depends": [
        "account",
        "configuration_helper",
        "currency_rate_inverted",
        "account_financial_report",
        "mis_builder",
        "mis_template_financial_report",
        "ssi_master_data_mixin",
    ],
    "data": [
        "security/ir_module_category_data.xml",
        "security/res_group_data.xml",
        "security/ir.model.access.csv",
        "data/account_journal_data.xml",
        "menu.xml",
        "views/res_config_settings_views.xml",
        "views/mis_report_instance_views.xml",
        "views/mis_report_style_views.xml",
        "views/mis_report_views.xml",
        "views/account_account_type_views.xml",
        "views/account_account_views.xml",
        "views/account_move_line_views.xml",
        "views/account_move_views.xml",
        "views/cash_flow_type_views.xml",
        "wizards/general_ledger_wizard_views.xml",
        "wizards/trial_balance_wizard_views.xml",
        "wizards/aged_partner_balance_wizard_views.xml",
        "report/templates/aged_partner_balance.xml",
    ],
    "demo": [],
}

# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Financial Accounting",
    "version": "14.0.2.1.0",
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
    ],
    "data": [
        "security/ir_module_category_data.xml",
        "security/res_group_data.xml",
        "menu.xml",
        "views/res_config_settings_views.xml",
        "views/mis_report_instance_views.xml",
        "wizards/general_ledger_wizard_views.xml",
        "wizards/trial_balance_wizard_views.xml",
        "wizards/aged_partner_balance_wizard_views.xml",
    ],
    "demo": [],
}

import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-open-synergy-ssi-financial-accounting",
    description="Meta package for open-synergy-ssi-financial-accounting Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-ssi_account_account_m2o_configurator_mixin',
        'odoo14-addon-ssi_account_create_liquidity_journal',
        'odoo14-addon-ssi_account_journal_m2o_configurator_mixin',
        'odoo14-addon-ssi_account_move_line_day_overdue',
        'odoo14-addon-ssi_account_move_py3o_report',
        'odoo14-addon-ssi_account_move_sequence',
        'odoo14-addon-ssi_account_statement_import',
        'odoo14-addon-ssi_account_type_active',
        'odoo14-addon-ssi_financial_accounting',
        'odoo14-addon-ssi_journal_entry_work_log',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)

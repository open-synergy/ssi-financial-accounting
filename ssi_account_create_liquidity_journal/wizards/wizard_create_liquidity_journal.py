# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0-standalone.html).

from odoo import fields, models


class WizardCreateLiquidityJournal(models.TransientModel):
    _name = "account.wizard_create_liquidity_journal"
    _description = "Create Liquidity Journal"

    liquidity_type = fields.Selection(
        string="Type",
        selection=[
            ("cash", "Cash"),
            ("bank", "Bank"),
        ],
        required=True,
    )
    two_step = fields.Boolean(
        string="Need Reconcilliation",
    )
    suspense_account_id = fields.Many2one(
        string="Suspense Account",
        comodel_name="account.account",
        required=True,
    )

    def action_confirm(self):
        for record in self:
            record._action_confirm()

    def _action_confirm(self):
        self.ensure_one()
        Account = self.env["account.account"]
        account_ids = self.env.context.get("active_ids", [])
        accounts = Account.browse(account_ids)
        for account in accounts:
            self._create_liquidity_journal(account)

    def _create_liquidity_journal(self, account):
        self.ensure_one()
        AccountJournal = self.env["account.journal"]
        AccountJournal.create(self._prepare_journal_data(account))

    def _prepare_journal_data(self, account):
        self.ensure_one()
        payment_account = self.suspense_account_id
        code = str(account.id).ljust(4, "0")
        if self.liquidity_type == "cash":
            code = "C" + code
        else:
            code = "B" + code

        if not self.two_step:
            payment_account = account
        result = {
            "name": account.name,
            "type": self.liquidity_type,
            "company_id": account.company_id.id,
            "currency_id": account.currency_id and account.currency_id.id or False,
            "default_account_id": account.id,
            "suspense_account_id": self.suspense_account_id.id,
            "payment_debit_account_id": payment_account.id,
            "payment_credit_account_id": payment_account.id,
            "code": code,
        }
        return result

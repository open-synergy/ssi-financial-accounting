# Copyright 2004-2020 Odoo S.A.
# Copyright 2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Licence AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def action_import_statement(self):
        for document in self:
            if document.journal_id:
                action = (
                    self.env.ref(
                        "account_statement_import.account_statement_import_action"
                    )
                    .sudo()
                    .read()[0]
                )
                action["context"] = {"journal_id": self.journal_id.id}
                return action

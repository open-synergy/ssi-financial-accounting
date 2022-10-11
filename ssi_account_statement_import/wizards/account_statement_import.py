# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import _, models
from odoo.exceptions import UserError


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def import_file_button(self):
        """Process the file chosen in the wizard, create bank statement(s)
        and return an action."""
        result = self._import_file()
        active_model = self.env.context.get("active_model", [])
        if active_model == "account.bank.statement":
            return True
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_bank_statement_tree"
            )
            if len(result["statement_ids"]) == 1:
                action.update(
                    {
                        "view_mode": "form,tree",
                        "views": False,
                        "res_id": result["statement_ids"][0],
                    }
                )
            else:
                action["domain"] = [("id", "in", result["statement_ids"])]
            return action

    def import_single_statement(self, single_statement_data, result):
        if not isinstance(single_statement_data, tuple):
            raise UserError(
                _("The parsing of the statement file returned an invalid result.")
            )
        currency_code, account_number, stmts_vals = single_statement_data
        # Check raw data
        if not self._check_parsed_data(stmts_vals):
            return False
        if not currency_code:
            raise UserError(_("Missing currency code in the bank statement file."))
        # account_number can be None (example : QIF)
        currency = self._match_currency(currency_code)
        journal = self._match_journal(account_number, currency)
        if not journal.default_account_id:
            raise UserError(
                _("The Bank Accounting Account in not set on the " "journal '%s'.")
                % journal.display_name
            )
        # Prepare statement data to be used for bank statements creation
        stmts_vals = self._complete_stmts_vals(stmts_vals, journal, account_number)

        active_model = self.env.context.get("active_model", [])
        if active_model == "account.bank.statement":
            # Update the bank statements
            self._update_bank_statements(stmts_vals, result)
        else:
            # Create the bank statements
            self._create_bank_statements(stmts_vals, result)
        # Now that the import worked out, set it as the bank_statements_source
        # of the journal
        if journal.bank_statements_source != "file_import":
            # Use sudo() because only 'account.group_account_manager'
            # has write access on 'account.journal', but 'account.group_account_user'
            # must be able to import bank statement files
            journal.sudo().write({"bank_statements_source": "file_import"})

    def _update_bank_statements(self, stmts_vals, result):
        """Create new bank statements from imported values,
        filtering out already imported transactions,
        and return data used by the reconciliation widget"""
        abs_obj = self.env["account.bank.statement"]
        absl_obj = self.env["account.bank.statement.line"]
        active_ids = self.env.context.get("active_ids", [])
        bank_statement = abs_obj.browse(active_ids)
        # Filter out already imported transactions and create statements
        statement_ids = []
        existing_st_line_ids = {}
        for st_vals in stmts_vals:
            st_lines_to_create = []
            for lvals in st_vals["transactions"]:
                existing_line = False
                if lvals.get("unique_import_id"):
                    existing_line = absl_obj.sudo().search(
                        [
                            ("unique_import_id", "=", lvals["unique_import_id"]),
                        ],
                        limit=1,
                    )
                    # we can only have 1 anyhow because we have a unicity SQL constraint
                if existing_line:
                    existing_st_line_ids[existing_line.id] = True
                    if "balance_start" in st_vals:
                        st_vals["balance_start"] += float(lvals["amount"])
                else:
                    st_lines_to_create.append(lvals)

            if len(st_lines_to_create) > 0:
                if not st_lines_to_create[0].get("sequence"):
                    for seq, vals in enumerate(st_lines_to_create, start=1):
                        vals["sequence"] = seq
                # Remove values that won't be used to create records
                st_vals.pop("transactions", None)
                # Create the statement with lines
                st_vals["line_ids"] = [[0, False, line] for line in st_lines_to_create]
                bank_statement.write({"line_ids": st_vals["line_ids"]})
                statement_ids.append(bank_statement.id)

        if not statement_ids:
            return False
        result["statement_ids"].extend(statement_ids)

        # Prepare import feedback
        num_ignored = len(existing_st_line_ids)
        if num_ignored > 0:
            result["notifications"].append(
                {
                    "type": "warning",
                    "message": _(
                        "%d transactions had already been imported and were ignored."
                    )
                    % num_ignored
                    if num_ignored > 1
                    else _("1 transaction had already been imported and was ignored."),
                    "details": {
                        "name": _("Already imported items"),
                        "model": "account.bank.statement.line",
                        "ids": list(existing_st_line_ids.keys()),
                    },
                }
            )

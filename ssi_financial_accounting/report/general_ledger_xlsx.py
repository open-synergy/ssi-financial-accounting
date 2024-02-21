# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class GeneralLedgerXslx(models.AbstractModel):
    _inherit = "report.a_f_r.report_general_ledger_xlsx"

    def _generate_report_content(self, workbook, report, data, report_data):
        res_data = self.env[
            "report.account_financial_report.general_ledger"
        ]._get_report_values(report, data)
        general_ledger = res_data["general_ledger"]
        accounts_data = res_data["accounts_data"]
        journals_data = res_data["journals_data"]
        taxes_data = res_data["taxes_data"]
        tags_data = res_data["tags_data"]
        filter_partner_ids = res_data["filter_partner_ids"]
        foreign_currency = res_data["foreign_currency"]
        # For each account
        for account in general_ledger:
            # Write account title
            total_bal_curr = account['init_bal'].get('bal_curr', 0)
            self.write_array_title(
                account["code"] + " - " + accounts_data[account["id"]]["name"],
                report_data,
            )

            if "list_grouped" not in account:
                # Display array header for move lines
                self.write_array_header(report_data)

                # Display initial balance line for account
                account.update(
                    {
                        "initial_debit": account["init_bal"]["debit"],
                        "initial_credit": account["init_bal"]["credit"],
                        "initial_balance": account["init_bal"]["balance"],
                    }
                )
                if foreign_currency:
                    account.update(
                        {"initial_bal_curr": account["init_bal"]["bal_curr"]}
                    )
                self.write_initial_balance_from_dict(account, report_data)

                # Display account move lines
                for line in account["move_lines"]:
                    line.update(
                        {
                            "account": account["code"],
                            "journal": journals_data[line["journal_id"]]["code"],
                        }
                    )
                    if line["currency_id"]:
                        line.update(
                            {
                                "currency_name": line["currency_id"][1],
                                "currency_id": line["currency_id"][0],
                            }
                        )
                    if line["ref_label"] != "Centralized entries":
                        taxes_description = ""
                        tags = ""
                        for tax_id in line["tax_ids"]:
                            taxes_description += taxes_data[tax_id]["tax_name"] + " "
                        if line["tax_line_id"]:
                            taxes_description += line["tax_line_id"][1]
                        for tag_id in line["tag_ids"]:
                            tags += tags_data[tag_id]["name"] + " "
                        line.update(
                            {
                                "taxes_description": taxes_description,
                                "tags": tags,
                            }
                        )
                    if foreign_currency:
                        total_bal_curr += line["bal_curr"]
                        line.update({"total_bal_curr": total_bal_curr})
                    self.write_line_from_dict(line, report_data)
                # Display ending balance line for account
                account.update(
                    {
                        "final_debit": account["fin_bal"]["debit"],
                        "final_credit": account["fin_bal"]["credit"],
                        "final_balance": account["fin_bal"]["balance"],
                    }
                )
                if foreign_currency:
                    account.update(
                        {
                            "final_bal_curr": account["fin_bal"]["bal_curr"],
                        }
                    )
                self.write_ending_balance_from_dict(account, report_data)

            else:
                # For each partner
                total_bal_curr = 0
                for group_item in account["list_grouped"]:
                    # Write partner title
                    self.write_array_title(group_item["name"], report_data)

                    # Display array header for move lines
                    self.write_array_header(report_data)

                    account.update(
                        {
                            "currency_id": accounts_data[account["id"]]["currency_id"],
                            "currency_name": accounts_data[account["id"]][
                                "currency_name"
                            ],
                        }
                    )

                    # Display initial balance line for partner
                    group_item.update(
                        {
                            "initial_debit": group_item["init_bal"]["debit"],
                            "initial_credit": group_item["init_bal"]["credit"],
                            "initial_balance": group_item["init_bal"]["balance"],
                            "type": "partner",
                            "grouped_by": account["grouped_by"]
                            if "grouped_by" in account
                            else "",
                            "currency_id": accounts_data[account["id"]]["currency_id"],
                            "currency_name": accounts_data[account["id"]][
                                "currency_name"
                            ],
                        }
                    )
                    if foreign_currency:
                        group_item.update(
                            {
                                "initial_bal_curr": group_item["init_bal"]["bal_curr"],
                            }
                        )
                    self.write_initial_balance_from_dict(group_item, report_data)

                    # Display account move lines
                    for line in group_item["move_lines"]:
                        line.update(
                            {
                                "account": account["code"],
                                "journal": journals_data[line["journal_id"]]["code"],
                            }
                        )
                        if line["currency_id"]:
                            line.update(
                                {
                                    "currency_name": line["currency_id"][1],
                                    "currency_id": line["currency_id"][0],
                                }
                            )
                        if line["ref_label"] != "Centralized entries":
                            taxes_description = ""
                            tags = ""
                            for tax_id in line["tax_ids"]:
                                taxes_description += (
                                    taxes_data[tax_id]["tax_name"] + " "
                                )
                            for tag_id in line["tag_ids"]:
                                tags += tags_data[tag_id]["name"] + " "
                            line.update(
                                {
                                    "taxes_description": taxes_description,
                                    "tags": tags,
                                }
                            )
                        if foreign_currency:
                            total_bal_curr += line["bal_curr"]
                            line.update({"total_bal_curr": total_bal_curr})
                        self.write_line_from_dict(line, report_data)

                    # Display ending balance line for partner
                    group_item.update(
                        {
                            "final_debit": group_item["fin_bal"]["debit"],
                            "final_credit": group_item["fin_bal"]["credit"],
                            "final_balance": group_item["fin_bal"]["balance"],
                        }
                    )
                    if foreign_currency and group_item["currency_id"]:
                        group_item.update(
                            {
                                "final_bal_curr": group_item["fin_bal"]["bal_curr"],
                            }
                        )
                    self.write_ending_balance_from_dict(group_item, report_data)

                    # Line break
                    report_data["row_pos"] += 1

                if not filter_partner_ids:
                    account.update(
                        {
                            "final_debit": account["fin_bal"]["debit"],
                            "final_credit": account["fin_bal"]["credit"],
                            "final_balance": account["fin_bal"]["balance"],
                        }
                    )
                    if foreign_currency and account["currency_id"]:
                        account.update(
                            {
                                "final_bal_curr": account["fin_bal"]["bal_curr"],
                            }
                        )
                    self.write_ending_balance_from_dict(account, report_data)

            # 2 lines break
            report_data["row_pos"] += 2

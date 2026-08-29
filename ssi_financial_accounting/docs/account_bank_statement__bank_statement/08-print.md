# Print Bank Statement

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Bank Statements\
> **Actor:** user in group \_Bank Statement — Viewer*\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** The record exists, in any status.
- **Data:** At least one `ir.actions.report` is registered for `account.bank.statement`
  (the **Statement** report from Odoo core is registered by default).
- **Access:** User is in group _Bank Statement — Viewer_
  (`ssi_financial_accounting.bank_statement_viewer_group`), or higher.

## Flow

1. Open the **Financial Accounting > Bank & Cash > Bank Statements** menu.
2. Open the record to print.
3. Click the **Print** button.
4. In the **Select Report To Print** wizard, select a **Type** (if more than one is
   available) and the **Report Template**.
5. Click **Print**.

## Post-Condition

- The selected report is generated and downloaded as a PDF.

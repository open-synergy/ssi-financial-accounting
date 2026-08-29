# Print Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — Viewer*\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** The record exists, in any status.
- **Data:** At least one `ir.actions.report` is registered for `account.bank.statement`
  (the **Statement** report from Odoo core is registered by default).
- **Access:** User is in group _Cash Register — Viewer_
  (`ssi_financial_accounting.cash_register_viewer_group`), or higher.

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Open the record to print.
3. Click the **Print** button.
4. In the **Select Report To Print** wizard, select a **Type** (if more than one is
   available) and the **Report Template**.
5. Click **Print**.

## Post-Condition

- The selected report is generated and downloaded as a PDF.

# Delete Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — User*\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **New**. A register that has been posted (or later) must first
  be reset to **New** — see `06-reset-to-new` — before it can be deleted.
- **Access:** User is in group _Cash Register — User_
  (`ssi_financial_accounting.cash_register_user_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Select one or more records to delete (check the checkbox).
3. Click **Action** > **Delete**.
4. Click **OK** to confirm.

## Post-Condition

- The selected records, and their transaction lines, are permanently removed from the
  system.

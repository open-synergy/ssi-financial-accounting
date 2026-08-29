# Edit Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — User*\
> **Requires:** `01-create`\
> **Inline Actions:** `action_reload_policy_template` (Reload Template Policy)

## Pre-Condition

- **Record:** Status is **New**.
- **Access:** User is in group _Cash Register — User_
  (`ssi_financial_accounting.cash_register_user_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Find and open the record to edit.
3. Change the required fields — **Journal**, **Date**, **Starting Balance**, **Ending
   Balance**, or the **Transactions** lines.
4. _(Optional, System group only)_ On the **Policies** tab, click **Reload Template
   Policy** to re-evaluate which `policy.template` applies to this document — for
   example after changing the **Journal**. Skipping this step leaves the currently
   assigned template unchanged.
5. Click **Save**.

## Post-Condition

- The record is updated with the new values.

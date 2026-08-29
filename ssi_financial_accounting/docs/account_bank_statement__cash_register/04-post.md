# Post Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — User*\
> **State:** `open` → `posted`\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **New**.
- **Config:** An active `policy.template` for this model grants `post_ok` for state
  `open` to the actor's group (`policy_template_bank_statement_cash`).
- **Access:** User is in group _Cash Register — User_
  (`ssi_financial_accounting.cash_register_user_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Open the record to post.
3. Click the **Post** button.

## Post-Condition

- Status changes to **Processing**.
- The register's document **Number** is generated (no longer **/**).
- The related journal entries of the transaction lines are posted.
- If the register has no transaction lines, it is automatically validated as well —
  status goes straight to **Validated** (see `05-validate`).

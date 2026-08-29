# Post Bank Statement

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Bank Statements\
> **Actor:** user in group \_Bank Statement — User*\
> **State:** `open` → `posted`\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **New**.
- **Config:** An active `policy.template` for this model grants `post_ok` for state
  `open` to the actor's group (`policy_template_bank_statement_bank`).
- **Access:** User is in group _Bank Statement — User_
  (`ssi_financial_accounting.bank_statement_user_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Bank Statements** menu.
2. Open the record to post.
3. Click the **Post** button.

## Post-Condition

- Status changes to **Processing**.
- The statement's document **Number** is generated (no longer **/**).
- The related journal entries of the transaction lines are posted.
- If the statement has no transaction lines, it is automatically validated as well —
  status goes straight to **Validated** (see `05-validate`).

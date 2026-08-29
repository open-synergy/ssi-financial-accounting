# Reset to New — Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — Validator*\
> **State:** `posted` → `open`\
> **Requires:** `04-post`

## Pre-Condition

- **Record:** Status is **Processing**.
- **Config:** An active `policy.template` for this model grants `reopen_ok` for state
  `posted` to the actor's group (`policy_template_bank_statement_cash`).
- **Access:** User is in group _Cash Register — Validator_
  (`ssi_financial_accounting.cash_register_validator_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Open the record to reset.
3. Click the **Reset to New** button.

## Post-Condition

- Status changes back to **New**.
- The related journal entries of the transaction lines are reset to draft.
- The reconciliation of the transaction lines is undone.

# Reset to New — Bank Statement

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Bank Statements\
> **Actor:** user in group \_Bank Statement — Validator*\
> **State:** `posted` → `open`\
> **Requires:** `04-post`

## Pre-Condition

- **Record:** Status is **Processing**.
- **Config:** An active `policy.template` for this model grants `reopen_ok` for state
  `posted` to the actor's group (`policy_template_bank_statement_bank`).
- **Access:** User is in group _Bank Statement — Validator_
  (`ssi_financial_accounting.bank_statement_validator_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Bank Statements** menu.
2. Open the record to reset.
3. Click the **Reset to New** button.

## Post-Condition

- Status changes back to **New**.
- The related journal entries of the transaction lines are reset to draft.
- The reconciliation of the transaction lines is undone.

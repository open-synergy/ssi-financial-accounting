# Validate Bank Statement

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Bank Statements\
> **Actor:** user in group \_Bank Statement — Validator*\
> **State:** `posted` → `confirm`\
> **Requires:** `04-post`

## Pre-Condition

- **Record:** Status is **Processing**.
- **Record:** At least one transaction line exists, and every line is reconciled.
- **Config:** An active `policy.template` for this model grants `validate_ok` for state
  `posted` to the actor's group, and requires all lines to be reconciled
  (`policy_template_bank_statement_bank`).
- **Access:** User is in group _Bank Statement — Validator_
  (`ssi_financial_accounting.bank_statement_validator_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Bank Statements** menu.
2. Open the record to validate.
3. Click the **Validate** button.

## Post-Condition

- Status changes to **Validated**.
- The **Closed On** date is set to the current date and time.
- For a Bank journal, a PDF copy of the statement is attached to the record.

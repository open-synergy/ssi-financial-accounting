# Validate Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — Validator*\
> **State:** `posted` → `confirm`\
> **Requires:** `04-post`

## Pre-Condition

- **Record:** Status is **Processing**.
- **Record:** At least one transaction line exists, and every line is reconciled.
- **Record:** The computed ending balance matches the **Ending Balance** entered on the
  register. If it does not match, a **difference confirmation** wizard opens instead of
  validating directly.
- **Config:** An active `policy.template` for this model grants `validate_ok` for state
  `posted` to the actor's group, and requires all lines to be reconciled
  (`policy_template_bank_statement_cash`).
- **Access:** User is in group _Cash Register — Validator_
  (`ssi_financial_accounting.cash_register_validator_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Open the record to validate.
3. Click the **Validate** button.

## Post-Condition

- Status changes to **Validated**.
- The **Closed On** date is set to the current date and time.

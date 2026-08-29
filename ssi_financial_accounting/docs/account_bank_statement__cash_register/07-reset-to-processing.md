# Reset to Processing — Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — User*\
> **State:** `confirm` → `posted`\
> **Requires:** `05-validate`

## Pre-Condition

- **Record:** Status is **Validated**.
- **Config:** An active `policy.template` for this model grants `reprocess_ok` for state
  `confirm` to the actor's group (`policy_template_bank_statement_cash`).
- **Access:** User is in group _Cash Register — User_
  (`ssi_financial_accounting.cash_register_user_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Open the record to reset.
3. Click the **Reset to Processing** button.

## Post-Condition

- Status changes back to **Processing**.
- The **Closed On** date is cleared.

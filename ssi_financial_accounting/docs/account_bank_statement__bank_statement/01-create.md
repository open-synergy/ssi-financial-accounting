# Create Bank Statement

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Bank Statements\
> **Actor:** user in group \_Bank Statement — User*\
> **State:** `—` → `open`\
> **Inline Actions:** `action_reload_policy_template` (Reload Template Policy)

## Pre-Condition

- **Data:** An `account.journal` of type **Bank** exists.
- **Access:** User is in group _Bank Statement — User_
  (`ssi_financial_accounting.bank_statement_user_group`).
- **Access:** User has full Accounting access (group _Show Full Accounting Features_,
  `account.group_account_user`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Bank Statements** menu.
2. Click the **New** button. **(14.0: "Create")**
3. Fill in the required fields:
   - **Journal**: select the Bank journal this statement belongs to. Only journals of
     type **Bank** are shown.
   - **Date**: defaults to today. Change if needed.
   - **Starting Balance**: defaults from the ending balance of the previous statement of
     the same journal. Change if needed.
   - **Ending Balance**: enter the real ending balance shown on the bank's statement.
4. _(Optional, System group only)_ On the **Policies** tab, click **Reload Template
   Policy** to re-evaluate which `policy.template` applies to this document. A matching
   template is already assigned automatically when the record is created; use this
   button only if something that affects the evaluation (e.g. the configured templates)
   changed afterward. Skipping this step leaves the automatically assigned template
   unchanged.
5. Click **Save**.

## Post-Condition

- A new record is created in **New** status.
- The document **Number** stays **/** until the statement is posted.

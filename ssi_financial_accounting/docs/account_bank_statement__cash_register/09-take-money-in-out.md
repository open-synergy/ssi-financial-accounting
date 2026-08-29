# Take Money In/Out — Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — User*\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **New** or **Processing** (not **Validated** — attempting this
  on a Validated register raises an error).
- **Data:** The register's company has an **Internal Transfer Account** configured
  (`res.company.transfer_account_id`).
- **Config:** An active `policy.template` for this model grants `cash_box_ok` to the
  actor's group for a Cash journal (`policy_template_bank_statement_cash`).
- **Access:** User is in group _Cash Register — User_
  (`ssi_financial_accounting.cash_register_user_group`).

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Open the register.
3. Click the **Take Money In/Out** button.
4. In the wizard that appears, fill in:
   - **Reason**: why money is being put into or taken from the cash box.
   - **Amount**: a positive amount adds money in, a negative amount takes money out.
5. Click **Take Money In/Out** to confirm, or **Cancel** to discard.

## Post-Condition

- A new transaction line is added to the register with the entered amount and reason.

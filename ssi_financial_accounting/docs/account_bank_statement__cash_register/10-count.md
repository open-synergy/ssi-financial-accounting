# Count — Cash Register

> **Module:** ssi*financial_accounting\
> **Model:** `account.bank.statement`\
> **Menu:** Financial Accounting > Bank & Cash > Cash Registers\
> **Actor:** user in group \_Cash Register — User*\
> **Requires:** `01-create`

## Pre-Condition

- **Record:** Status is **New**.

## Flow

1. Open the **Financial Accounting > Bank & Cash > Cash Registers** menu.
2. Open the register.
3. Click **Edit**. The **→ Count** link is only shown while the form is in edit mode.
4. Next to **Starting Balance** or **Ending Balance**, click **→ Count**.
5. In the cash-count wizard, for each coin/note denomination counted, click **Add a
   line** and fill in:
   - **Coin/Bill Value**: the denomination's value (e.g. `50000`, `1000`, `500`).
   - **#Coins/Bills**: how many pieces of that denomination were counted. The
     **Subtotal** per line and the **Total** at the bottom are calculated automatically.
6. Click **Confirm** to apply the counted total to the balance, or **Cancel** to
   discard.

## Post-Condition

- The **Starting Balance** (or **Ending Balance**, depending on which **→ Count** link
  was used) is set to the counted **Total**.

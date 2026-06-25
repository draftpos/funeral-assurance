# Funeral Assurance System - Implementation Plan

## 1. Accounting Integration (In Progress / Next Step)
**Goal:** Automate Sales Invoices based on Policy Status.
* Add `account` dependency to `__manifest__.py`.
* Override `funeral.policy` state transition (when activated) to automatically create a `res.partner` (Customer) linked to the `funeral.proposal`.
* Implement an Odoo Cron Job (`ir.cron`) to run monthly, iterate over all `active` policies, and generate a draft `account.move` (Sales Invoice) based on the `premium_amount`.

## 2. Massive Reports Generation (Pending)
**Goal:** Implement the 100+ required SQL/ORM reports across the 15 categories.
* **Clients Management:** New Clients, Demographics, Age Analysis, Dependants, Beneficiaries, etc.
* **Policies Management:** Active, Lapsed, Cancelled, Suspended, Underwriting, Accepted, Growth, Anniversary, Movement, Audit.
* **Premiums Collections:** Daily, Monthly, Summarized, Cash, Debit Order, Stop Order, Arrears, Success/Failure Rates, Agent/Branch Analysis.
* **Debtors Management:** Outstanding Premium Debtors, Age Analysis, Bad Debt, Payment History.
* **Claims Management:** Open, Closed, Pending, Approved, Rejected, Branch/Agent/Product Analysis, Turnaround Time, Actuary Structure.
* **Funerals Management:** Detailed, Upcoming, Completed, Cost Analysis, Profitability, Burial/Cremation Details, Police B11.
* **Burial Societies:** Listing, Members, Collections, Arrears, Claims, Payments, Growth.
* **New Business Management:** Summaries, Overpayments, Underwriter Collections, Product Profitability.
* **Commissions Management:** Agent/Broker Statements, Branch Summaries, Outstanding.
* **Tombstones:** Orders (Pending/Completed), Debtors, Suppliers, Profitability, Sales Analysis.
* **Services/Stock:** Levels, Movement, Valuation, Issues, Purchases, Usage, Audit.
* **Users & Audit:** Activity, Login, Audit Trail, Deleted Records, Security Audit.
* **Financial Reports:** Income, Expense, Profitability, Cash Flow, Revenue Analysis.
* **Dashboard Reports:** KPIs, Branch Comparison, Agent Performance, Executive Summaries.
* **Vehicles:** Master List, Usage, Booking, Mileage, Fuel Consumption, Maintenance, Driver Reports, Compliance (Licence Expiry), Financial Operating Costs.

**Implementation Strategy:** Each report will require a custom `ir.actions.report` and either a QWeb PDF template or an `ir.actions.act_window` linked to a heavily customized Pivot/Graph/List view grouping the data. 

## 3. Print Formats & PDF Receipts (Pending Images)
* **Images 6 & 7 needed:** Standard Claim, Private Claim, and Assured Claim.
* Once provided, we will rewrite `claim_view.xml` and `reports/sum_assured_claim.xml` using exact HTML tabular structures (`border-collapse`) to perfectly map the fields to the physical forms, exactly as was done for the Proposal and Payment forms.

## 4. Module Finalization
* **Stock Management:** The base models and views (`funeral.stock.type`, `funeral.stock.item`, `funeral.stock.transaction`) have been scaffolded. We need to finalize inventory adjustment logic and stock valuation.
* **Vehicles Management:** Further refine the existing vehicle models to support specific fields (Licence Expiry, Mileage, Services) required by the Vehicle Reports section.
* **Tombstone Management:** Expand the existing Tombstone forms to track supplier info, specific prices, and installation steps required for the Tombstone Reports.
* **Commissioner Module:** Flesh out the Actuaries and Auditors data processing forms.

## Note on Deployment
For every major block of reports added, the module should be upgraded via the command line (`python odoo-bin -c odoo.conf -u funeral_assurance`) while the server is stopped to avoid database locking (`SerializationFailure`).

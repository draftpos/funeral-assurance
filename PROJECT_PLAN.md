# Funeral Assurance Project Plan & Business Specifications

This document serves as the master blueprint for the Funeral Assurance Odoo module, outlining the core business rules, commission structures, policy monitoring, and product configurations.

## 1. Commission Logic & Agent Structures
Commissions are strictly calculated and paid based on active/paid business; no commissions are executed for accepted or Non-Taken Up (NTU) business. Payments are distributed on a monthly basis.

### General Agents
- **Commission Rate:** 33.33% per month.
- **Duration:** Paid out over a fixed period of 3 months (99.99% total payout).
- **Condition:** Premium must be successfully collected on a monthly basis to trigger that month's payout. If a client misses a payment, no commission is paid for that month.

### Executive Agents
- **Commission Rate:** 33.33% calculated once-off based on performance.
- **Threshold Condition:** 
  - The system evaluates the agent's total first-month premium payments collected within the calendar month.
  - Up to the first $200 of collected premium acts as a standard allowance and does not yield percentage commissions.
  - For any volume collected above $200, a 33.33% commission is calculated on the excess amount.
- **Reset Cycle:** The calculation volume resets to zero at the beginning of each calendar month (e.g., resetting on 1 July).

### Office Agents
- **Commission Rate:** 33.33% calculated once-off.
- **Condition:** Applied directly to the first payment volume collected, without a minimum allowance threshold or rolling multi-month cycles.

---

## 2. Policy Monitoring, Lapses, & Clawbacks

### Policy Tracker (Months Paid Counter)
To prevent the system from over-executing payouts, the Policy Details database requires a Months Paid counter field.
- **Tracking:** Increment the field with each verified monthly premium receipt (1 → 2 → 3).
- **Stop Trigger:** When the counter hits 3, the commission engine must automatically skip this policy in future loops.
- **Sync Loop:** If a policy has a counter of 1 or 2, the engine inspects the verified transaction history for that period; if a payment is found, the counter increments and the commission fires.

### Lapses
If a policy remains unpaid for 4 consecutive months, it changes status to Lapsed.

### Clawback Mechanism
To protect cash flows from early cancellations and to encourage agents to prevent policies from dropping off, the system enforces a strict clawback protocol:
- **Trigger:** If a policy lapses within its active commission window, previous payouts must be clawed back.
- **Execution:** The engine retracts funds at the same rate and frequency they were given (33.33% per month for the months paid).
- **UI Representation:** Do not subtract this implicitly from a database array. The clawback must render explicitly on the Commission Statement UI as a separate line item mapping to the original policy (e.g., *John Banda | Clawback Status | -$5.00*). It will deduct natively from their net payout for that period.

---

## 3. Status Upgrade Architecture
The system must execute a Status Update Routine before running the monthly commission processing. This routine evaluates policy health flags chronologically to ensure no money is spent on invalid accounts.

```text
[System Evaluation Loop] 
       │
       ▼
 1. Check Payments ───► If none found ───► Set to "Accepted"
       │
       ▼
 2. Check Overdue Status ───► If unresolved ───► Change from "Accepted" to "NTU"
       │
       ▼
 3. Check 4-Month Horizon ───► If unpaid ───► Set to "Lapsed"
       │
       ▼
 4. Final Processing ───► Filter Active/Live ───► Process Commission Engine
```

---

## 4. Claims Processing Workflow
When a policyholder passes away, the claim capture process follows a distinct administrative flow to ensure quick payout verification:
- **Status Tagging:** The user flags the primary policyholder or verified dependent as Deceased.
- **Claim Logging:** The system opens a dynamic form requiring explicit tracking details:
  - Deceased individual's full name.
  - Cause and place of death (Hospital vs. Home).
- **Verification Matrix:** The module determines if the claim successfully falls within mature, active terms or faces policy exceptions. Once passed, the claim status upgrades to approved for disbursement.

---

## 5. Product Configuration Matrix 

### The "O" Plan
The "O" Plan serves as the primary multi-tenant product engine, containing nested sub-plans dynamically mapped to functional benefits, premiums, and cash-benefit limits.

| Sub-Plan Name | Structural Type | Premium | Ext. Family Top-Up | Sum Assured | Grocery Benefit | Coffin/Casket Spec |
|---|---|---|---|---|---|---|
| Bronze Plan | Member Only | $15.00 | $2.00 | $100.00 | $50.00 | Standard Casket |
| Silver Plan | Member Only | $24.00 | $2.00 | $120.00 | $60.00 | Two-Tier Casket |
| Diamond Plan | Member Only | $27.00 | $2.00 | $130.00 | $70.00 | Three-Tier Casket |
| Platinum/Gold | Member Only | $33.00 | $2.00 | $150.00 | $90.00 | Dome-Shape Casket |
| Bronze Plan | Family Only | $18.00 | $2.00 | $100.00 | $50.00 | Standard Casket |
| Silver Plan | Family Only | $23.00 | $2.00 | $120.00 | $60.00 | Two-Tier Casket |
| Diamond Plan | Family Only | $29.00 | $2.00 | $130.00 | $70.00 | Three-Tier Casket |
| Platinum/Gold | Family Only | $39.00 | $2.00 | $150.00 | $90.00 | Dome-Shape Casket |
| Bronze Plan | Family + 4 Parents | $33.00 | $2.00 | $120.00 | $70.00 | Standard Casket |
| Silver Plan | Family + 4 Parents | $38.00 | $2.00 | $140.00 | $80.00 | Two-Tier Casket |
| Diamond Plan | Family + 4 Parents | $44.00 | $2.00 | $150.00 | $90.00 | Three-Tier Casket |
| Platinum/Gold | Family + 4 Parents | $50.00 | $2.00 | $170.00 | $110.00 | Dome-Shape Casket |

### Alternative Fixed-Structure Products
Unlike the flexible nested options of the "O" Plan, these corporate and institutional plans operate on hard-coded rules:
- **Hukama Plan:** $20.00 Premium, $2.00 Extended family top-up, $120.00 Sum Assured, and $60.00 Grocery. Standard Casket template applies.
- **Gutsarushinji Plan:** $38.00 Premium, $2.00 Extended family top-up, $150.00 Sum Assured, and $100.00 Grocery. Dome-Shape Casket template applies.
- **ZPCS / SSB / Civil Servant Plans:** Hard-coded to parallel each other. The premium is $21.00, Sum Assured is $120.00, and Grocery Benefit is $75.00. Extended family members can be attached indefinitely at $2.00 per head. Uses a Two-Tier Casket configuration.
- **ZENE Plan (20-year maturity timeline):**
  - Standard: $15.00 Premium, $100.00 Sum Assured, and $50.00 Grocery benefit.
  - Two-Tier: $20.00 Premium, $150.00 Sum Assured, and $60.00 Grocery benefit.
  - Dome: $25.00 Premium, $200.00 Sum Assured, and $70.00 Grocery benefit.
- **Gogo neVazukuru:** Custom specialized matrix.

### Corporate Group Plan (Minimum 20 Members)
- **Structure:** Requires a minimum baseline of 20 active members to execute the group rate.
- **Premium:** Structured on a flat, group-wide distribution of $2.00 per individual member.
- **Payout Terms:** Features instant cover properties upon validation of the first cluster payment. Payouts scale dynamically based on member-to-dependent relationships registered under the corporate profile.

---

## 6. Database Implementation Strategy
To prevent code fragility when introducing new insurance products down the line, keep this structure highly parameter-driven rather than hard-coding schemas. The sub-plans, premiums, and limits should map as variable data properties in local database files, enabling the multi-tenant engine to effortlessly scale as new corporate clients are onboarded.

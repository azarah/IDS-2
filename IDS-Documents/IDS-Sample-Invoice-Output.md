# IDS — Sample Invoice Output

**Prepared for:** Individualized Doula Services (IDS)

This appendix shows **example invoice text** produced by the shipped application **without interactive input**. Generate the same artifact at any time with:

```powershell
python IDS_Invoice_Application.py --demo
```

(requires standard data files beside the script: `IDS-Clients.txt`, `IDS-Doulas.txt`, `IDS-Rates.txt`).

---

## Scenario

Demo mode builds a hypothetical billing period invoice for sample client **KE20** (Ill Patterson) with:

- Telephone follow-up (**flat base rate × 2**)  
- Hospital labor support (**4 hours** × hospital hourly rate)  
- **18 miles** at the agreed mileage rate  
- Home recovery (**2 hours** × home hourly rate)

Actual names, addresses, totals, and `billing_period` label derive from **your live `IDS-*` files** at run time.

---

## Example output (KE20 roster as bundled in repo)

Generated on request via `--demo`; reproduced here for IDS documentation.

```
==============================================================
INDIVIDUALIZED DOULA SERVICES (IDS) - CLIENT INVOICE
==============================================================

Billing period: Q1 2026

Patient (client) information
------------------------------------------
  Client ID:    KE20
  Name:         Illy Patterson
  Address:      456 s Kick Lane, Chicago, IL 60629
  Phone:        616-930-2343
  Assigned doula ID: 4823

Charges
------------------------------------------
  Base (telephone / flat) subtotal            $200.00

  Telephone (flat-rate) assignments
    * Telephone - Follow-up - Doula 4823
        Code Doula_Tele01_FollowUp  x 2 @ $100.00  =  $200.00

  Additional services (home, hospital, mileage, overnight, etc.)
    * Hospital - Labor support - Doula 4823
        Code Doula_Hos01_LaborSupport  x qty 4 @ $50.00  =  $200.00
    * Mileage (agreed rate per mile) - Doula 4823
        Code IDS_Mileage  x qty 18 @ $0.73  =  $13.05
    * Home - Recovery - Doula 4823
        Code Doula_Home04_Recovery  x qty 2 @ $50.00  =  $100.00

  Additional services subtotal                $313.05

------------------------------------------
  TOTAL DUE (billing period)                  $513.05
==============================================================
```

---

## Notes for reviewers

1. **`$200.00` base**: two telephone assignment units × tele base rate from `IDS-Rates.txt`.  
2. **Mile line total `$13.05`**: eighteen miles × per-mile decimal (shown rounded to `$0.73` unit display × quantity).  
3. **TOTAL DUE** is the arithmetic sum printed by the application for that billing period—acceptance tests during handoff typically compare **`--demo`** output after rates file confirmation.

---

*This document fulfills IDS-Requirements.md: Implementation — “supply a separate document with an example of the output.”*

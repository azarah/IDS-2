# IDS — Requirements Analysis

**Prepared for:** Individualized Doula Services (IDS)  
**Prepared by:** Zarah Sharda  
**Reference:** IDS-Requirements.md

---

## 1. Organizational need

IDS is a practice that hires trained female personnel to provide **pre- and post-delivery doula services**. Staff must maintain current CPR certification and tolerate irregular hours. The firm bills **telephone (remote) support** at a **flat base rate**, while **home and hospital visits** are billed **hourly**, separate from that base.

The company needed a dependable way to **track work attributed to assignments** from the agreed service menu (`IDS-Rates.txt`) and to give each client a **period invoice** listing patient information, base cost (telephone/flat assignments), additional services with costs, and **total due**—without deploying server infrastructure.

A secondary organizational goal is to **reduce conflict and administrative friction** between doulas, clients, and administration by treating services as clearly coded **assignments** tied to **recorded profiles** and **doula–client assignments** in text files.

---

## 2. Requirements list (summarized)

| ID | Requirement |
|----|----------------|
| R1 | Produce a client invoice containing patient (mother) information. |
| R2 | Show base cost aligned with telephone/flat-rate services. |
| R3 | List additional services rendered with individual costs (home/hospital hourly, mileage, overnight, etc.). |
| R4 | Show total amount due for the billing period. |
| R5 | Operate **without** server-side components (local execution). |
| R6 | Use Python as the delivered program, with overview and inline documentation. |
| R7 | Maintain doula and client **profiles** in external files (`IDS-Doulas.txt`, `IDS-Clients.txt`): ID, names, addresses, phones; CPR certification expiry for doulas only. |
| R8 | Maintain **rates and billing period label** in `IDS-Rates.txt`, including mileage as agreed. |
| R9 | Encode **which doula is assigned to which client** in client records to avoid ambiguity. |
| R10 | Support **client** entry (by Client ID), **doula** entry (by Doula ID, then pick assigned client(s)), and an **admin** view of roster activity. |
| R11 | User experience should feel **supportive and assistive** while remaining transactional enough for billing. |

---

## 3. What the system must **do**

- **Authenticate by ID** using Client ID, Doula ID, or Administrator (via `IDS-Admin.txt`; `Admin` always allowed).
- **Load** client roster, doula roster, and rate table from text files beside the script.
- **Guide** users through hierarchical menus (Telephone → flat; Hospital/Home → hourly; Other → mileage/overnight), with optional shortcuts and direct service-code entry for power users.
- **Prompt** for quantities: counts for flat assignments, hours for hourly services, miles for mileage.
- **Calculate** line totals using `Decimal` for currency precision; sum **base** (telephone) and **additional** subtotals and **grand total**.
- **Preview** the invoice at the terminal and optionally **save** as `invoice_<ClientID>.txt` in the application folder.
- **Allow** adding more lines after preview without restarting the session context.
- **Admin mode:** display client records and doula roster with assignments; flag clients whose assigned doula ID lacks a matching doula profile.
- **Demonstration:** `python IDS_Invoice_Application.py --demo` prints a sample invoice for documentation.

---

## 4. What the system must **have** (capabilities & assets)

### 4.1 Data the system consumes

- **Clients:** comma-separated rows with Client ID, name, address fields, phone, **assigned Doula ID** (`IDS-Clients.txt`).
- **Doulas:** comma-separated rows with Doula ID, name, location/phone fragments, CPR certification note (`IDS-Doulas.txt`).
- **Rates:** keyed values for `tele_base`, `home_rate_per_hr`, `hospital_rate_per_hr`, mileage, overnight, optional `billing_period_label` (`IDS-Rates.txt`).
- **Admin IDs (optional):** extra administrator sign-ins beyond literal `Admin` (`IDS-Admin.txt`).

### 4.2 Built-in artifacts

- A **service catalog** mapping IDS assignment codes (aligned to `IDS-Rates.txt`) to human-readable labels and pricing **kinds** (flat tele, hourly hospital, hourly home, per-mile, overnight flat).
- **Default rate fallbacks** if the rates file is missing or incomplete.

### 4.3 Runtime environment

- **Python 3** on a Windows (or comparable) workstation; **no database**, **no network service** required for core billing.

### 4.4 Outputs

- **Screen:** formatted invoice text and onboarding/help tables (`Help` at IDS ID prompt).
- **Disk (optional):** UTF-8 text invoice file named per client ID.

---

*This analysis satisfies the Requirements Analysis phase described in IDS-Requirements.md.*

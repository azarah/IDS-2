# IDS — Implementation Overview

**Prepared for:** Individualized Doula Services (IDS)  
**Program:** `IDS Invoice Application/IDS_Invoice_Application.py`

This document summarizes the shipped Python solution. **Inline documentation** (module docstring, section comments, and function docstrings) lives in `IDS_Invoice_Application.py` and is authoritative for programmers.

---

## 1. What the program does

`IDS_Invoice_Application.py` loads local text files defining **clients**, **doulas**, **rates**, and optional **extra admin IDs**, then drives an interactive **command-line session**:

- **Clients** identify with their **Client ID** and build an invoice for themselves; the app greets them and shows **assigned doula** when the roster resolves.
- **Doulas** identify with **Doula ID**, see everyone assigned to them in `IDS-Clients.txt`, pick the client for this invoice, and enter line items (their profile is stamped on assignment rows when resolved).
- **Administrators** use `Admin` or IDs listed in `IDS-Admin.txt` to view **client activity** and **doula activity** (including assignment lists and orphaned references).

Assignments are picked from hierarchical menus keyed to IDS service codes consistent with **`IDS-Rates.txt`**.

---

## 2. Running the application

Change to the folder containing `IDS_Invoice_Application.py` (or pass full path):

```powershell
python IDS_Invoice_Application.py
```

| Mode | Command | Behavior |
|------|-----------|----------|
| Interactive | `python IDS_Invoice_Application.py` | Full sign-in → line-item loop → preview → optional save → optional add more lines |
| Demo | `python IDS_Invoice_Application.py --demo` | Builds a deterministic sample invoice for client `KE20` (fallback to first client / synthetic demo row) and prints to stdout |

At the **IDS ID** prompt:

- **`Help`** — prints doula/client ID reference tables (`*` hints for unassigned doulas or clients missing assigned doula).
- **Blank input** — exit gracefully.

---

## 3. Input files

All paths are resolved relative to the script directory (`Path(__file__).parent`):

| File | Purpose |
|------|---------|
| `IDS-Clients.txt` | One client per line after header comment; CSV with Client ID, name, street, city, state ZIP, phone, **Doula ID** |
| `IDS-Doulas.txt` | Doula CSV-style rows parsed with tolerant phone/state-zip inference; last field = certification note |
| `IDS-Rates.txt` | `key=value` style rates and optional commented `billing_period_label` |
| `IDS-Admin.txt` | Optional extra administrator IDs (`Admin` always valid) |

If `IDS-Rates.txt` omits keys, **defaults** embedded in source apply (`DEFAULT_*` constants).

Minimum runtime guard: **at least one client** must load or the program exits with an error (`--demo` still runs parsers but sample needs a roster or synthesizes fallback).

---

## 4. Key implementation fragments (by concern)

### 4.1 Service catalog & menus

Codes like `Doula_Tele01_FollowUp` map to **`(label, kind)`** tuples in `SERVICE_CATALOG`; `prompt_service_code_choice()` walks categories Telephone / Hospital / Home / Other, supports **`2,3`**-style shortcuts, and accepts typed full codes.

### 4.2 Money arithmetic

Uses Python `decimal.Decimal` everywhere money is totaled to avoid floating-point rounding errors (`money()` formats for display).

### 4.3 Invoice semantics

**Base** equals the sum of `tele_flat` line items—the **Telephone assignments** grouping on the invoice. **Additional services** aggregates hospital, home, mileage, overnight, etc.

### 4.4 Output file naming

Sanitized **`invoice_<ClientID>.txt`** with characters unsafe under Windows filenames replaced.

---

## 5. Where to read more detail in code

| Topic | Locate in |
|-------|-----------|
| Parsing rates | `parse_rates_file()` |
| Client/doula CSV logic | `_parse_client_line`, `_parse_doula_line` |
| Pricing | `unit_price_for()`, `make_line_item()` |
| Invoice text | `format_invoice()` |
| Main orchestration | `interactive_build()`, `main()` |

---

*This satisfies the Implementation deliverable (“overview” alongside inline documentation per IDS-Requirements.md). For a printed example, see IDS-Sample-Invoice-Output.md.*

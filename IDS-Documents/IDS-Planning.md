# IDS — Planning Document

**Prepared for:** Individualized Doula Services (IDS)  
**Prepared by:** Zarah Sharda  
**Reference:** IDS-Requirements.md

---

## 1. What is proposed and why

**Proposal.** Deliver a **single-file Python application** (`IDS_Invoice_Application.py`) bundled with editable **comma-separated profile and rate files**. The application runs locally, guides clients and doulas through recording billable assignments, and produces **client invoices** that separate **telephone (base/flat)** work from **visit and other** charges.

**Why this approach.**

- Fits IDS’s constraint of **no server-side** deployment—no hosting fees, TLS certificates, or database administration for a small practice.
- **Text files as system of record** let administrators update rosters and agreed rates **without programmer involvement**.
- **Pre-assigned doula on each client row** aligns billing with operational truth and lowers disputes over “whose” line items are credited.
- **One program, multiple roles** (client sign-in, doula sign-in, admin overview) keeps training and deployment simple versus maintaining separate billing engines.

---

## 2. Software, hardware, and personnel implications

### 2.1 Software

| Item | Role |
|------|------|
| **Python 3.11+** (recommended) | Runtime for the invoicing script. |
| **Standard library only** (current deliverable) | No third-party installs required for MVP. |
| **Text editor** (Notepad++, VS Code, etc.) | Edit `IDS-Clients.txt`, `IDS-Doulas.txt`, `IDS-Rates.txt`, `IDS-Admin.txt`. |

No commercial license purchases are mandatory for this solution.

### 2.2 Hardware

- **Staff PC(s)** sufficient to run Python and store the application folder (including invoice outputs). Typical office or laptop hardware is adequate.
- **Optional:** shared network folder or practice-approved cloud sync if invoices must be centralized (operational decision; not enforced by software).

### 2.3 Personnel changes

| Role | Change |
|------|--------|
| **Administrator** | Continues owning master data files (clients, doulas, rates); may add optional admin IDs. |
| **Doulas** | May enter line items via Doula ID when building invoices for assigned clients—**light training** on menus and quantities. |
| **Clients** | May use Client ID for self-service preview/save paths—optional; brief orientation on prompts. |
| **IT / vendor (Zarah Sharda)** | Initial setup, documentation handoff; ongoing support per maintenance agreement (see IDS-Maintenance-and-Support.md). |

---

## 3. Approach and roadmap to solution

| Phase | Activity | Outcome |
|-------|-----------|---------|
| **Discovery** | Confirm invoice layout, rate model, assignment rules | Requirements analysis locked |
| **Planning** | Lock file formats, personas, deployment model | Planning sign-off |
| **Design** | Data model, menus, invoice formatter, admin views, security posture | Specs + diagrams |
| **Implementation** | Python module with parsers, catalogs, CLI flow, `--demo` | Runnable application |
| **Verification** | Run `--demo`; walk through client/doula/admin paths | Acceptance examples |
| **Handoff & support** | Train administrators; define maintenance boundaries | Operational runbook |

Iterations already reflected in the product: hierarchical menus → keyboard shortcuts → **assignment-driven identity** → unified invoice generator for client and doula sessions.

---

## 4. Modularization and coupling

### 4.1 Modular breakdown (conceptual compartments)

Despite a single `.py` file, the codebase is compartmentalized by concern:

| Compartment | Responsibility |
|-------------|----------------|
| **I/O parsing** | `parse_rates_file`, `load_clients`, `load_doulas`, `load_admin_ids` |
| **Domain model** | `Client`, `Doula`, `RateTable`, `LineItem`, `Invoice` dataclasses |
| **Pricing** | `SERVICE_CATALOG`, `unit_price_for`, `make_line_item` |
| **UI / flow** | `interactive_build`, `_run_invoice_editing_loop`, `prompt_service_code_choice`, `run_admin_dashboard` |
| **Presentation** | `format_invoice`, helpers for activity reports and help table |

Future enhancement (recommended in IDS-Implementation-Strategy-Report.md): extract **`ids_core.py`** shared library if secondary entry scripts appear—today everything is deliberately **low coupling** to the filesystem paths adjacent to `__file__`.

### 4.2 Interactivity (“coupling” between modules)

- **Tight cohesion:** parsers produce dataclass instances consumed only by invoicing logic—clear data contracts.
- **Loose coupling to UI:** `format_invoice(inv)` renders any built `Invoice` object; demos and saved files share the same function.
- **External coupling:** filenames (`IDS-Clients.txt`, etc.) are **conventions**; changing names requires matching code edits unless parameterized later.

This structure supports predictable maintenance without over-engineering a small-firm prototype.

---

*This document satisfies the Planning phase described in IDS-Requirements.md.*

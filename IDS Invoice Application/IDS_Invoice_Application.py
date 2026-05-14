#!/usr/bin/env python3
"""
Programmer           :  Charletta Hudson
Date of Submission   :  6 May 2026
Course               :  CIS 245 - Principles of Software Development
Instructor           :  Charles McSweeney

Program Name: IDS Invoice Application

Program Description:

Individualized Doula Services (IDS) — Invoice application
=========================================================

Purpose
-------
This module implements a locally run billing assistant for IDS. It loads roster and pricing
data from companion text files, guides clients or doulas through assigning billable services
from the firm's menu, and produces a standardized client invoice. Administrators may view summary
reports of client and doula assignments. Processing requires no hosted server — all logic
resides in this file alongside the configured data paths.

Operational summary
-------------------
- Data sources: ``IDS-Clients.txt``, ``IDS-Doulas.txt``, ``IDS-Rates.txt``, optional ``IDS-Admin.txt``.
- Sign-in: **Client ID**, **Doula ID**, or **Admin** (``Admin`` is always valid; see admin file).
- Outputs: Terminal preview of the invoice and, on confirmation, ``invoice_<ClientID>.txt`` beside this script.

Usage
-----
    python IDS_Invoice_Application.py        # interactive invoice session
    python IDS_Invoice_Application.py --demo # print sample invoice (documentation / QA)

Enter ``Help`` at the IDS ID prompt for roster reference tables.

Resolution note: After administration sign-in is ruled out, if the same identifier existed as both
client and doula — which the roster should prevent — client sign-in takes precedence.

Data files omit optional keys sensibly when absent (defaults documented under rate configuration).
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Standard library
# -----------------------------------------------------------------------------
import argparse
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum, auto
from pathlib import Path

# =============================================================================
# Configuration: default rates and billable service catalog
# =============================================================================
# Values below align with ``IDS-Rates.txt`` when that file is missing or incomplete.
# The catalog maps each IDS assignment code to a display label and pricing category (``kind``).
# =============================================================================
DEFAULT_TELE_BASE = Decimal("100")
DEFAULT_HOME_HOSPITAL_PER_HR = Decimal("50")
DEFAULT_MILEAGE_PER_MILE = Decimal("0.725")  # 72.5 cents
DEFAULT_OVERNIGHT = Decimal("400")
DEFAULT_BILLING_LABEL = "Q1 2026"

# Each catalog entry: official IDS code → (customer-facing label, internal pricing kind).
# ``kind`` selects which rate from ``RateTable`` applies: flat telephone, hourly venue, per mile, etc.
SERVICE_CATALOG: dict[str, tuple[str, str]] = {
    # Telephone (flat tele_base each)
    "Doula_Tele01_FollowUp": ("Telephone - Follow-up", "tele_flat"),
    "Doula_Tele02_Support": ("Telephone - Support", "tele_flat"),
    "Doula_Tele03_Reminders": ("Telephone - Reminders", "tele_flat"),
    "Doula_Tele04_Paperwork": ("Telephone - Paperwork", "tele_flat"),
    "Doula_Tele05_Education": ("Telephone - Education", "tele_flat"),
    "Doula_Tele06_Resources": ("Telephone - Resources", "tele_flat"),
    # Hospital (per hour)
    "Doula_Hos01_LaborSupport": ("Hospital - Labor support", "hourly_hospital"),
    "Doula_Hos02_Advocacy": ("Hospital - Advocacy", "hourly_hospital"),
    "Doula_Hos03_Coaching": ("Hospital - Coaching", "hourly_hospital"),
    "Doula_Hos04_Bedside": ("Hospital - Bedside", "hourly_hospital"),
    "Doula_Hos05_Logistics": ("Hospital - Logistics", "hourly_hospital"),
    # Home (per hour)
    "Doula_Home01_FollowUp": ("Home - Follow-up", "hourly_home"),
    "Doula_Home02_Support": ("Home - Support", "hourly_home"),
    "Doula_Home03_LaborSupport": ("Home - Labor support", "hourly_home"),
    "Doula_Home04_Recovery": ("Home - Recovery", "hourly_home"),
    "Doula_Home05_Education": ("Home - Education", "hourly_home"),
    # Other billable from rates file
    "IDS_Mileage": ("Mileage (agreed rate per mile)", "mileage"),
    "IDS_Overnight": ("Overnight", "overnight"),
}


# =============================================================================
# Assignment selection: category menus and submenus
# =============================================================================
# Guides the operator through Telephone / Hospital / Home / Other groupings aligned with IDS
# rate documentation.
# =============================================================================


def _menu_label_for_code(code: str) -> str:
    """Returns a shortened label for submenu display (trimmed Telephone/Hospital/Home prefix)."""
    full, _kind = SERVICE_CATALOG[code]
    for prefix in ("Telephone - ", "Hospital - ", "Home - "):
        if full.startswith(prefix):
            return full[len(prefix) :]
    return full


def _service_codes_telephone() -> list[str]:
    return sorted(k for k in SERVICE_CATALOG if k.startswith("Doula_Tele"))


def _service_codes_hospital() -> list[str]:
    return sorted(k for k in SERVICE_CATALOG if k.startswith("Doula_Hos"))


def _service_codes_home() -> list[str]:
    return sorted(k for k in SERVICE_CATALOG if k.startswith("Doula_Home"))


def _service_codes_other() -> list[str]:
    return [k for k in ("IDS_Mileage", "IDS_Overnight") if k in SERVICE_CATALOG]


# Single-letter shortcuts at the category prompt (t telephone, h hospital, r residence/home, o other).
_CATEGORY_ALIASES = {"t": "1", "h": "2", "r": "3", "o": "4"}


def _normalize_category_digit(raw: str) -> str:
    """Normalize category input to digit ``1``–``4`` (accepts aliases t, h, r, o)."""
    r = raw.strip()
    if len(r) == 1 and r.lower() in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[r.lower()]
    return r


class _SubmenuResult(Enum):
    BACK = auto()
    DONE_ADDING = auto()


# Outer assignment menu uses 1–4 for categories; option 5 (or blank) ends line-item entry.
_MAIN_MENU_DONE_NUM = 5


def _prompt_submenu(codes: list[str], title: str) -> str | _SubmenuResult:
    """Presents numbered services within one category until the operator exits or completes entry."""
    done_num = len(codes) + 1
    while True:
        print(f"\n{title}")
        print("-" * 42)
        for i, code in enumerate(codes, start=1):
            print(f"  {i} - {_menu_label_for_code(code)}")
        print(f"  {done_num} - Done adding line items")
        print("  0 - Exit")
        raw = input("Enter number: ").strip()
        if raw == "0":
            return _SubmenuResult.BACK
        if raw == str(done_num):
            return _SubmenuResult.DONE_ADDING
        if not raw.isdigit():
            print("  Please enter a number from the list.")
            continue
        n = int(raw)
        if 1 <= n <= len(codes):
            return codes[n - 1]
        print(f"  Invalid choice. Enter 0-{done_num}.")


def prompt_service_code_choice() -> str | None:
    f"""
    Drives the top-level category loop, then the appropriate submenu.

    Returns a billable service code, or ``None`` when the operator finishes the line-item list.
    Option {_MAIN_MENU_DONE_NUM}, ``0`` (exit), or an empty line ends category selection.

    Within a submenu, ``0`` returns to categories; the trailing option marks done adding items.
    """
    pick_map = {
        "1": (_service_codes_telephone(), "1 - Telephone assignments"),
        "2": (_service_codes_hospital(), "2 - Hospital assignments"),
        "3": (_service_codes_home(), "3 - Home assignments"),
        "4": (_service_codes_other(), "4 - Other charges"),
    }
    while True:
        print("\nChoose Assignment from Category:")
        print("-" * 42)
        print("  1 - Telephone (flat rate per assignment)")
        print("  2 - Hospital (hourly)")
        print("  3 - Home (hourly)")
        print("  4 - Other (mileage, overnight)")
        print(f"  {_MAIN_MENU_DONE_NUM} - Done adding line items")
        print("  0 - Exit")
        raw = input("Choice: ").strip()
        if not raw or raw == str(_MAIN_MENU_DONE_NUM) or raw == "0":
            return None
        if raw in SERVICE_CATALOG:
            return raw

        # --- Category + row jump (e.g. "2,4", "h 3") ---------------------------------
        jm = re.match(
            r"^([1-4]|[throTHRO])[, ]\s*(\d+)\s*$",
            raw,
        )
        if jm:
            cat_key = _normalize_category_digit(jm.group(1))
            sub_n = int(jm.group(2))
            entry = pick_map.get(cat_key)
            if not entry:
                continue
            codes, _st = entry
            if 1 <= sub_n <= len(codes):
                return codes[sub_n - 1]
            print(f"  Enter 1-{len(codes)} for that category.")
            continue

        cat_key = _normalize_category_digit(raw)
        entry = pick_map.get(cat_key)
        if not entry:
            print(
                f"  Not a valid category (1-4), or {_MAIN_MENU_DONE_NUM}/0 when finished. Try again."
            )
            continue
        codes, sub_title = entry
        if not codes:
            print("  No services in that category.")
            continue
        chosen = _prompt_submenu(codes, sub_title)
        if chosen is _SubmenuResult.DONE_ADDING:
            return None
        if chosen is _SubmenuResult.BACK:
            continue
        return chosen


# =============================================================================
# Domain model: roster entities, rates, invoice structure
# =============================================================================
# Structured records used throughout parsing, pricing, and invoice rendering. ``Invoice`` splits
# telephone (flat) charges from all other line types for statement presentation.
# =============================================================================


@dataclass
class Client:
    """IDS family account as stored per row in ``IDS-Clients.txt``."""

    client_id: str
    name: str
    address: str
    phone: str
    assigned_doula_id: str | None = None


@dataclass
class Doula:
    """Care provider profile as interpreted from ``IDS-Doulas.txt``."""

    doula_id: str
    name: str
    address: str
    phone: str
    certification_note: str


@dataclass
class RateTable:
    """Financial parameters loaded from ``IDS-Rates.txt`` (with sane defaults when absent)."""

    tele_base: Decimal
    home_rate_per_hr: Decimal
    hospital_rate_per_hr: Decimal
    mileage_rate_per_mile: Decimal
    overnight_rate: Decimal
    billing_period_label: str


@dataclass
class LineItem:
    """Single billable assignment: code, descriptive label, rate category, quantities, extended price."""

    service_code: str
    description: str
    kind: str
    quantity: Decimal  # Hours or miles where applicable; count of flat units for telephone/overnight.
    unit_price: Decimal
    line_total: Decimal
    doula_id: str | None = None
    doula_name: str | None = None


@dataclass
class Invoice:
    """Current billing run: one client, one period label, and zero or more line items."""

    billing_period: str
    client: Client
    items: list[LineItem] = field(default_factory=list)

    def base_subtotal(self) -> Decimal:
        """Returns the subtotal for telephone (flat-rate) assignments — the invoice 'base' section."""
        return sum(
            (li.line_total for li in self.items if li.kind == "tele_flat"),
            start=Decimal("0"),
        )

    def additional_subtotal(self) -> Decimal:
        """Returns the subtotal for all non-telephone charges (visits, mileage, overnight, etc.)."""
        return sum(
            (li.line_total for li in self.items if li.kind != "tele_flat"),
            start=Decimal("0"),
        )

    def total(self) -> Decimal:
        """Grand total for the billing period (sum of all line items)."""
        return sum((li.line_total for li in self.items), start=Decimal("0"))


# =============================================================================
# Presentation utilities and safe output filenames
# =============================================================================


def money(d: Decimal) -> str:
    """Formats a ``Decimal`` as a U.S.-style currency string for display and saved invoices."""
    q = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"${q:,.2f}"


def script_dir() -> Path:
    """Directory containing this script (data files and saved invoices resolve here)."""
    return Path(__file__).resolve().parent


def invoice_filename_for_client(client_id: str) -> str:
    """Builds ``invoice_<ClientID>.txt``, replacing characters invalid on Windows file systems."""
    cleaned = "".join(
        c if c not in '<>:"/\\|?*' else "_"
        for c in client_id.strip()
    )
    if not cleaned:
        cleaned = "client"
    return f"invoice_{cleaned}.txt"


# =============================================================================
# Rate configuration: ``IDS-Rates.txt``
# =============================================================================
# Reads key/value style lines; supports billing period label. Mileage accepts cents-style input
# (values greater than 1 are interpreted as whole cents and converted to dollars per mile).
# =============================================================================


def parse_rates_file(path: Path) -> RateTable:
    """Constructs a ``RateTable`` from file content, retaining module defaults where keys are absent."""
    t = RateTable(
        tele_base=DEFAULT_TELE_BASE,
        home_rate_per_hr=DEFAULT_HOME_HOSPITAL_PER_HR,
        hospital_rate_per_hr=DEFAULT_HOME_HOSPITAL_PER_HR,
        mileage_rate_per_mile=DEFAULT_MILEAGE_PER_MILE,
        overnight_rate=DEFAULT_OVERNIGHT,
        billing_period_label=DEFAULT_BILLING_LABEL,
    )
    if not path.is_file():
        return t
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            # Standalone billing-period line: ``billing_period_label = Q1 2026`` (comment may follow).
            m = re.match(r"^billing_period_label\s*=\s*(.+)$", line, re.I)
            if m:
                t.billing_period_label = m.group(1).strip()
            continue
        key, _, rest = line.partition("=")
        key = key.strip().lower()
        val = re.sub(r"[^\d.]", "", rest)  # dollars or cents numeric part
        if not val:
            continue
        d = Decimal(val)
        if key == "tele_base":
            t.tele_base = d
        elif key == "home_rate_per_hr":
            t.home_rate_per_hr = d
        elif key == "hospital_rate_per_hr":
            t.hospital_rate_per_hr = d
        elif "mileage" in key:
            # file says 72.5 cents — stored as 0.725 if parsed alone
            if d > 1:
                t.mileage_rate_per_mile = d / Decimal("100")
            else:
                t.mileage_rate_per_mile = d
        elif key == "overnight_rate":
            t.overnight_rate = d
    return t


# =============================================================================
# Roster ingestion: ``IDS-Clients.txt`` and ``IDS-Doulas.txt``
# =============================================================================
# Comma-separated rows; comment lines and header-like first cells are skipped. Doula rows tolerate
# variable column ordering by detecting phone and state/ZIP patterns within the middle fields.
# =============================================================================


_PHONE_RE = re.compile(r"^\d{3}-\d{3}-\d{4}$")
_STATE_ZIP_RE = re.compile(r"^[A-Z]{2}\s+\d{5}$", re.I)
_CSV_HEADER_FIRST_CELL = re.compile(r"(?i)^(client|doula)s?\s+id#$")


def _parse_client_line(line: str) -> Client | None:
    """Return a ``Client`` from one comma-separated ``IDS-Clients.txt`` row, or ``None`` if skipped."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 6:
        return None
    cid = parts[0]
    if _CSV_HEADER_FIRST_CELL.match(cid.strip()):
        return None
    name, street, city, state_zip, phone = parts[1], parts[2], parts[3], parts[4], parts[5]
    address = f"{street}, {city}, {state_zip}"
    doula_id: str | None = None
    if len(parts) >= 7 and parts[6]:
        doula_id = parts[6]
    return Client(
        client_id=cid,
        name=name,
        address=address,
        phone=phone,
        assigned_doula_id=doula_id,
    )


def _parse_doula_line(line: str) -> Doula | None:
    """Return a ``Doula`` from one comma-separated ``IDS-Doulas.txt`` row; tolerates uneven column spacing."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 4:
        return None
    did = parts[0]
    if _CSV_HEADER_FIRST_CELL.match(did.strip()):
        return None
    cert = parts[-1]
    inner = parts[1:-1]
    if not inner:
        return None
    name = inner[0]
    phone: str | None = None
    state_zip: str | None = None
    for p in inner[1:]:
        if _PHONE_RE.match(p):
            phone = p
        if _STATE_ZIP_RE.match(p):
            state_zip = p
    addr_parts = [
        p for p in inner[1:] if p != phone and p != state_zip
    ]
    address = ", ".join(addr_parts)
    if state_zip:
        address = f"{address}, {state_zip}" if address else state_zip
    if phone is None:
        phone = ""
    return Doula(doula_id=did, name=name, address=address, phone=phone, certification_note=cert)


def load_clients(path: Path) -> dict[str, Client]:
    """Loads all clients keyed by ``client_id`` from the given roster path (empty dict if unreadable)."""
    out: dict[str, Client] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        c = _parse_client_line(line)
        if c:
            out[c.client_id] = c
    return out


def load_doulas(path: Path) -> dict[str, Doula]:
    """Loads all doulas keyed by ``doula_id`` from the given roster path."""
    out: dict[str, Doula] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        d = _parse_doula_line(line)
        if d:
            out[d.doula_id] = d
    return out


# =============================================================================
# Pricing and line-item construction
# =============================================================================


def unit_price_for(kind: str, rates: RateTable) -> Decimal:
    """Returns the unit rate from ``rates`` for a catalog ``kind`` (telephone, hourly, mileage, etc.)."""
    if kind == "tele_flat":
        return rates.tele_base
    if kind == "hourly_home":
        return rates.home_rate_per_hr
    if kind == "hourly_hospital":
        return rates.hospital_rate_per_hr
    if kind == "mileage":
        return rates.mileage_rate_per_mile
    if kind == "overnight":
        return rates.overnight_rate
    raise ValueError(f"Unknown kind: {kind}")


def clients_assigned_to_doula(clients: dict[str, Client], doula_id: str) -> list[Client]:
    """Lists clients whose assigned doula identifier matches ``doula_id`` (exact string match)."""
    return sorted(
        (c for c in clients.values() if c.assigned_doula_id == doula_id),
        key=lambda x: x.client_id,
    )


def load_admin_ids(path: Path) -> set[str]:
    """
    Returns permitted administrator sign-in strings (lowercased). The literal ``Admin`` is always
    valid; ``IDS-Admin.txt`` may list one supplemental identifier per non-comment line.
    """
    allowed: set[str] = {"admin"}
    if not path.is_file():
        return allowed
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        allowed.add(line.lower())
    return allowed


# =============================================================================
# Administrative views and operator reference
# =============================================================================
# Read-only summaries for roster review; no invoice modification from this path.
# =============================================================================


def _print_client_activity(clients: dict[str, Client], doulas: dict[str, Doula]) -> None:
    print("\nClient activity — all records (IDS-Clients.txt)")
    print("-" * 62)
    if not clients:
        print("  (no clients loaded)")
        return
    for c in sorted(clients.values(), key=lambda x: x.client_id):
        aid = c.assigned_doula_id or "—"
        extra = ""
        if c.assigned_doula_id:
            dprof = doulas.get(c.assigned_doula_id)
            if dprof:
                extra = f" — doula name: {dprof.name}"
            else:
                extra = " — doula profile missing from IDS-Doulas.txt"
        print(f"  {c.client_id} — {c.name}")
        print(f"      Phone:    {c.phone}")
        print(f"      Address:  {c.address}")
        print(f"      Assigned doula ID: {aid}{extra}")
        print()


def _print_doula_activity(clients: dict[str, Client], doulas: dict[str, Doula]) -> None:
    print("\nDoula activity — roster and assigned clients")
    print("-" * 62)
    if not doulas:
        print("  (no doulas loaded from IDS-Doulas.txt)")
    else:
        for d in sorted(doulas.values(), key=lambda x: x.doula_id):
            mine = clients_assigned_to_doula(clients, d.doula_id)
            print(f"  Doula ID {d.doula_id} — {d.name}")
            print(f"      Phone:   {d.phone}")
            print(f"      Address: {d.address}")
            if not mine:
                print("      Assigned clients: (none)")
            else:
                print(f"      Assigned clients ({len(mine)}):")
                for c in mine:
                    print(f"        • {c.client_id} — {c.name}")
            print()

    orphans = sorted(
        (
            c
            for c in clients.values()
            if c.assigned_doula_id and c.assigned_doula_id not in doulas
        ),
        key=lambda x: x.client_id,
    )
    # --- Data quality: client rows referencing a missing doula profile ----------------
    if orphans:
        print("  Clients whose assigned doula ID has no profile in IDS-Doulas.txt:")
        for c in orphans:
            print(f"    • {c.client_id} — {c.name}  →  doula ID {c.assigned_doula_id}")
        print()


def run_admin_dashboard(clients: dict[str, Client], doulas: dict[str, Doula]) -> None:
    """Simple menu loop for administrator review of client and doula roster information."""
    while True:
        print("\nAdministration — IDS overview")
        print("-" * 42)
        print("  1 - Client activity (all client records)")
        print("  2 - Doula activity (doulas and assignments)")
        print("  0 - Quit")
        raw = input("Choice: ").strip()
        if raw == "0":
            print("Goodbye.")
            return
        if raw == "1":
            _print_client_activity(clients, doulas)
        elif raw == "2":
            _print_doula_activity(clients, doulas)
        else:
            print("  Invalid choice.")


def _print_help_ids_table(clients: dict[str, Client], doulas: dict[str, Doula]) -> None:
    """Prints aligned ID and name tables for use at the initial sign-in prompt (``Help`` command)."""
    w_id, w_name = 14, 36
    sep = "+" + "-" * (w_id + 2) + "+" + "-" * (w_name + 2) + "+"

    def row(id_val: str, name: str, star_unassigned: bool) -> None:
        tid = id_val[:w_id].ljust(w_id)
        label = f"* {name}" if star_unassigned else name
        tname = label[:w_name].ljust(w_name)
        print(f"| {tid} | {tname} |")

    print("\nIDS ID reference — Doulas (IDS-Doulas.txt)")
    print(sep)
    print(f"| {'Doula ID'.ljust(w_id)} | {'Name'.ljust(w_name)} |")
    print(sep)
    if not doulas:
        print(f"| {'(none)'.ljust(w_id)} | {'—'.ljust(w_name)} |")
    else:
        for d in sorted(doulas.values(), key=lambda x: x.doula_id):
            no_clients = not clients_assigned_to_doula(clients, d.doula_id)
            row(d.doula_id, d.name, no_clients)
    print(sep)
    print("\nIDS ID reference — Clients (IDS-Clients.txt)")
    print(sep)
    print(f"| {'Client ID'.ljust(w_id)} | {'Name'.ljust(w_name)} |")
    print(sep)
    if not clients:
        print(f"| {'(none)'.ljust(w_id)} | {'—'.ljust(w_name)} |")
    else:
        for c in sorted(clients.values(), key=lambda x: x.client_id):
            aid = (c.assigned_doula_id or "").strip()
            no_doula = not aid
            row(c.client_id, c.name, no_doula)
    print(sep)
    print("\n  * Doula: no client lists this doula as assigned in IDS-Clients.txt.")
    print("  * Client: no assigned doula ID on this client's record.")
    print("")


def prompt_client_for_doula_session(doula: Doula, my_clients: list[Client]) -> Client | None:
    """
    When a doula supports multiple families, asks which client this invoice covers; a single
    assignment is selected automatically. Returns ``None`` if the operator chooses Quit.
    """
    if not my_clients:
        return None
    if len(my_clients) == 1:
        c = my_clients[0]
        print(f"\nThis invoice will be for your assigned client: {c.name} (Client ID {c.client_id}).")
        return c
    print(f"\nYou have {len(my_clients)} assigned clients. Which client is this invoice for?")
    print("-" * 42)
    for i, c in enumerate(my_clients, start=1):
        print(f"  {i} - {c.name} (ID {c.client_id})")
    print("  0 - Quit")
    while True:
        raw = input("Enter number: ").strip()
        if raw == "0":
            return None
        if not raw.isdigit():
            print("  Enter a number from the list.")
            continue
        n = int(raw)
        if 1 <= n <= len(my_clients):
            return my_clients[n - 1]
        print("  Invalid choice.")


def make_line_item(
    service_code: str,
    quantity: Decimal,
    rates: RateTable,
    doula: Doula | None = None,
    doula_id_if_unresolved: str | None = None,
) -> LineItem:
    """
    Builds one priced line from a catalog code and quantity. ``doula`` supplies attribution when
    the profile resolves; ``doula_id_if_unresolved`` preserves the identifier from the client
    roster when no matching doula record exists.
    """
    if service_code not in SERVICE_CATALOG:
        raise KeyError(f"Unknown service code: {service_code}")
    label, kind = SERVICE_CATALOG[service_code]
    unit = unit_price_for(kind, rates)
    if kind in ("tele_flat", "overnight"):
        # Flat-rate kinds: line total = unit price × count of billable units for this code.
        total = unit * quantity
    else:
        # Hospital, home (hourly), and mileage lines use unit rate × hours or × miles respectively.
        total = unit * quantity
    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    did = doula.doula_id if doula else doula_id_if_unresolved
    dname = doula.name if doula else None
    return LineItem(
        service_code=service_code,
        description=label,
        kind=kind,
        quantity=quantity,
        unit_price=unit,
        line_total=total,
        doula_id=did,
        doula_name=dname,
    )


# =============================================================================
# Invoice document layout (plain-text rendering)
# =============================================================================
# Structured client-facing wording: patient block, base telephone subtotal, itemized additions, totals.
# =============================================================================


def format_invoice(inv: Invoice) -> str:
    """Renders ``inv`` as the fixed IDS invoice layout (suitable for screen display or UTF-8 file)."""
    c = inv.client
    lines: list[str] = []
    # --- Banner and billing period -------------------------------------------------
    lines.append("=" * 62)
    lines.append("INDIVIDUALIZED DOULA SERVICES (IDS) - CLIENT INVOICE")
    lines.append("=" * 62)
    lines.append("")
    lines.append(f"Billing period: {inv.billing_period}")
    lines.append("")
    # --- Patient identification ----------------------------------------------------
    lines.append("Patient (client) information")
    lines.append("-" * 42)
    lines.append(f"  Client ID:    {c.client_id}")
    lines.append(f"  Name:         {c.name}")
    lines.append(f"  Address:      {c.address}")
    lines.append(f"  Phone:        {c.phone}")
    if c.assigned_doula_id:
        lines.append(f"  Assigned doula ID: {c.assigned_doula_id}")
    lines.append("")
    # --- Charges: base telephone, then additional services -------------------------
    lines.append("Charges")
    lines.append("-" * 42)
    lines.append(f"  {'Base (telephone / flat) subtotal':<40} {money(inv.base_subtotal()):>10}")
    lines.append("")
    lines.append("  Telephone (flat-rate) assignments")
    tele = [li for li in inv.items if li.kind == "tele_flat"]
    if not tele:
        lines.append("    (none this period)")
    for li in tele:
        who = f" - Doula {li.doula_id}" if li.doula_id else ""
        lines.append(f"    * {li.description}{who}")
        lines.append(
            f"        Code {li.service_code}  x {li.quantity} @ {money(li.unit_price)}  =  {money(li.line_total)}"
        )
    lines.append("")
    lines.append("  Additional services (home, hospital, mileage, overnight, etc.)")
    # Non–telephone items: hourly visits, mileage, overnight flat, etc.
    if not any(li.kind != "tele_flat" for li in inv.items):
        lines.append("    (none)")
    for li in inv.items:
        if li.kind == "tele_flat":
            continue
        who = f" - Doula {li.doula_id}" if li.doula_id else ""
        lines.append(f"    * {li.description}{who}")
        lines.append(
            f"        Code {li.service_code}  x qty {li.quantity} @ {money(li.unit_price)}  =  {money(li.line_total)}"
        )
    lines.append("")
    lines.append(f"  {'Additional services subtotal':<40} {money(inv.additional_subtotal()):>10}")
    lines.append("")
    # --- Closing totals ------------------------------------------------------------
    lines.append("-" * 42)
    lines.append(f"  {'TOTAL DUE (billing period)':<40} {money(inv.total()):>10}")
    lines.append("=" * 62)
    return "\n".join(lines)


# =============================================================================
# Interactive billing session (client, doula, or prior admin exit)
# =============================================================================


def _run_invoice_editing_loop(
    invoice: Invoice,
    rates: RateTable,
    acting_doula: Doula | None,
    doula_id_if_unresolved: str | None,
) -> None:
    """
    Presents the assignment menus until the operator finishes; shows a draft invoice; offers
    optional save to disk and further line-item rounds without losing context.
    """
    out_name = invoice_filename_for_client(invoice.client.client_id)
    while True:
        print(
            "\nUse the category menus. Tip: Enter the number that corresponds to the Assignment "
            "you are requesting from the Categories.\n"
        )

        # --- Line-item capture phase ---------------------------------------------------
        while True:
            code = prompt_service_code_choice()
            if not code:
                break
            _, kind = SERVICE_CATALOG[code]

            if kind in ("tele_flat", "overnight"):
                qtxt = input("Quantity (number of visits/units) [1]: ").strip() or "1"
            elif kind == "mileage":
                qtxt = input("Miles: ").strip() or "0"
            else:
                qtxt = input("Hours [1]: ").strip() or "1"

            try:
                qty = Decimal(qtxt)
            except Exception:
                print("  Invalid number; skipped.")
                continue
            if qty <= 0:
                print("  Quantity must be positive; skipped.")
                continue
            try:
                item = make_line_item(
                    code,
                    qty,
                    rates,
                    acting_doula,
                    doula_id_if_unresolved=doula_id_if_unresolved,
                )
            except Exception as e:
                print(f"  Error: {e}")
                continue
            invoice.items.append(item)
            print(f"  Added {money(item.line_total)} - {item.description}")

        # --- Review, optional save, continuation --------------------------------------
        print()
        print(format_invoice(invoice))
        save = input(
            f"\nSave invoice to {out_name} in the script folder? [y/N]: "
        ).strip().lower()
        if save == "y":
            out = script_dir() / out_name
            out.write_text(format_invoice(invoice), encoding="utf-8")
            print(f"Wrote {out}")

        more = input("\nAdd more line items to this invoice? [y/N]: ").strip().lower()
        if more != "y":
            print("\nThank you for using IDS. Goodbye.")
            break


def interactive_build(
    clients: dict[str, Client],
    doulas: dict[str, Doula],
    rates: RateTable,
) -> None:
    """
    Primary operator flow: IDS identifier entry, branching to administrator dashboard, client
    invoice session, or doula-led invoice session depending on validated roster lookups.
    """
    print()
    print("=" * 62)
    print("  Welcome to Individualized Doula Services (IDS)")
    print("=" * 62)
    print(
        "We are glad you are here. This tool is intended to help you record requests "
        "and view your invoice.\n"
    )
    print("Please Enter your IDS ID to build your Invoice. Press Enter to Quit.")
    print("Type Help for a table of Doula and Client IDs.")
    # --- Credential collection (supports Help repeat) ----------------------------
    while True:
        ids_raw = input("IDS ID: ").strip()
        if not ids_raw:
            print("Goodbye.")
            return
        if ids_raw.lower() == "help":
            _print_help_ids_table(clients, doulas)
            continue
        break

    admin_ids = load_admin_ids(script_dir() / "IDS-Admin.txt")
    # --- Administrator path --------------------------------------------------------
    if ids_raw.lower() in admin_ids:
        print("\nWelcome, Administrator.")
        run_admin_dashboard(clients, doulas)
        return

    client_row = clients.get(ids_raw)
    doula_row = doulas.get(ids_raw)

    # --- Client sign-in path -------------------------------------------------------
    if client_row is not None:
        client = client_row
        assigned_doula: Doula | None = None
        if client.assigned_doula_id:
            assigned_doula = doulas.get(client.assigned_doula_id)
            if assigned_doula:
                print(
                    f"\nWelcome, {client.name}. Your assigned doula is "
                    f"{assigned_doula.name} (ID {assigned_doula.doula_id})."
                )
            else:
                print(
                    f"\nWelcome, {client.name}. Note: doula ID {client.assigned_doula_id} "
                    "from your record was not found in IDS-Doulas.txt; line items will still "
                    "list that ID if shown."
                )
        else:
            print(
                f"\nWelcome, {client.name}. No assigned doula is on file for this client ID."
            )

        invoice = Invoice(billing_period=rates.billing_period_label, client=client)
        _run_invoice_editing_loop(
            invoice,
            rates,
            acting_doula=assigned_doula,
            doula_id_if_unresolved=(
                client.assigned_doula_id if not assigned_doula else None
            ),
        )
        return

    # --- Doula sign-in path --------------------------------------------------------
    if doula_row is not None:
        logged_in = doula_row
        did = logged_in.doula_id
        my_clients = clients_assigned_to_doula(clients, did)
        if not my_clients:
            print(
                f"\nWelcome, {logged_in.name}. No clients in IDS-Clients.txt are assigned "
                f"to doula ID {did}. Goodbye."
            )
            return

        print(
            f"\nWelcome, {logged_in.name}. You signed in as doula (ID {logged_in.doula_id})."
        )
        print("Your assigned client(s) in IDS records:")
        for c in my_clients:
            print(f"  - {c.name}  |  Client ID {c.client_id}")

        client = prompt_client_for_doula_session(logged_in, my_clients)
        if not client:
            print("Goodbye.")
            return

        invoice = Invoice(billing_period=rates.billing_period_label, client=client)
        _run_invoice_editing_loop(
            invoice,
            rates,
            acting_doula=logged_in,
            doula_id_if_unresolved=None,
        )
        return

    # --- Unrecognized identifier ---------------------------------------------------
    print(
        f"\nNo matching Client ID or Doula ID found for {ids_raw!r}. "
        "Check IDS-Clients.txt and IDS-Doulas.txt (or type Help / sign in as Admin). Goodbye."
    )


# =============================================================================
# Demonstration output and program entry
# =============================================================================


def demo_invoice(clients: dict[str, Client], doulas: dict[str, Doula], rates: RateTable) -> str:
    """
    Assembles a representative invoice (telephone, hospital, mileage, home) for grading,
    documentation screen shots, or quick regression checks. Prefers client ``KE20`` when present.
    """
    c = clients.get("KE20") or next(iter(clients.values()), None)
    if not c:
        c = Client(
            "DEMO",
            "Example Client",
            "123 Main St, Chicago, IL 60601",
            "555-0100",
            assigned_doula_id="4823",
        )
    d = doulas.get(c.assigned_doula_id) if c.assigned_doula_id else None
    unresolved = c.assigned_doula_id if (c.assigned_doula_id and not d) else None
    inv = Invoice(billing_period=rates.billing_period_label, client=c)
    inv.items.append(make_line_item("Doula_Tele01_FollowUp", Decimal("2"), rates, d, unresolved))
    inv.items.append(make_line_item("Doula_Hos01_LaborSupport", Decimal("4"), rates, d, unresolved))
    inv.items.append(make_line_item("IDS_Mileage", Decimal("18"), rates, d, unresolved))
    inv.items.append(make_line_item("Doula_Home04_Recovery", Decimal("2"), rates, d, unresolved))
    return format_invoice(inv)


def main() -> None:
    """Loads local data files, executes ``--demo`` or launches the interactive billing session."""
    ap = argparse.ArgumentParser(
        description=(
            "IDS client invoice assistant: sign in with a Client ID, Doula ID, or Administrator keyword."
        )
    )
    ap.add_argument("--demo", action="store_true", help="print a sample invoice and exit")
    args = ap.parse_args()

    base = script_dir()
    # --- Load authoritative text sources -------------------------------------------
    rates = parse_rates_file(base / "IDS-Rates.txt")
    clients = load_clients(base / "IDS-Clients.txt")
    doulas = load_doulas(base / "IDS-Doulas.txt")

    if args.demo:
        print(demo_invoice(clients, doulas, rates))
        return

    if not clients:
        print("No clients loaded from IDS-Clients.txt.", file=sys.stderr)
        sys.exit(1)
    if not doulas:
        print(
            "Warning: No doulas loaded from IDS-Doulas.txt — Doula ID sign-in will not work.",
            file=sys.stderr,
        )

    interactive_build(clients, doulas, rates)


if __name__ == "__main__":
    main()

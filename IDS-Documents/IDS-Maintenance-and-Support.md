# IDS — Maintenance and Support

**Prepared for:** Individualized Doula Services (IDS)  
**Vendor:** Zarah Sharda  
**Reference:** IDS-Requirements.md

---

## 1. Proposed agreement (maintenance & support)

The following reflects a **recommended baseline** for a small local Python tool. Final terms belong in IDS’s procurement or vendor statement of work.

| Term | Recommendation |
|------|----------------|
| **Warranty period** | **90 calendar days** from formal acceptance (“go-live”), covering **critical defects**: inability to launch, crashing after valid data entry, or invoice totals materially wrong versus agreed rate rules. |
| **Support channels** | Email/ticket preferred; optionally scheduled monthly check-in calls for the first quarter. |
| **Response targets** | **Business days only**: acknowledge within **1–2 days** (non-emergency); **critical** invoice math bugs targeted **within 5 business days** for fix or rollback guidance. |
| **What is excluded** | New features (GUIs, web hosting, integrations), user error from edited files, workstation OS/Python corruption, antivirus false positives deleting scripts, simultaneous multi-user concurrency on shared writable files beyond agreed design. |
| **Escalated changes** | Billed separately as **minor enhancement** vs **major initiative** upon written approval. |

This product was delivered as **requirements-aligned source + data files**. Backup of those assets remains **IDS’s operational responsibility**, with vendor-assisted restore instructions on request within the agreement window.

---

## 2. Proposed ongoing activities **after acceptance**

On behalf of IDS (subject to IDS approval and compensation where applicable):

1. **Version compatibility advisory** — when Python/OS upgrades are planned, advise on retesting `IDS_Invoice_Application.py` and dependencies (currently standard library only).
2. **Data format consulting** — help interpret parse warnings (e.g., malformed CSV lines) introduced by spreadsheet exports.
3. **Rate change validation** — double-check edits to `IDS-Rates.txt` against expected invoice totals for a canned `--demo`-style sanity check scenario.
4. **Security housekeeping reminders** — annual nudge about workstation disk encryption and physical access to invoice folders containing PII.
5. **Optional enhancement backlog grooming** — if IDS later adopts `ids_core`-style refactoring, GUI wrappers, or read-only validator passes, prioritize with IDS leadership.

Routine **data entry remains IDS’s daily operation** unless contracted separately.

---

## 3. Operational precautions for IDS operators

Observe these precautions whenever running or maintaining the system:

| Precaution | Rationale |
|------------|-----------|
| **Keep originals** of `IDS-Clients.txt` and `IDS-Doulas.txt` under dated backups **before bulk edits.** | Parsing depends on textual structure—rollback may be impossible without snapshots. |
| **Edit files in UTF-8** when saving from Excel or Google Sheets **without breaking comma columns.** | Truncated lines may drop doula IDs silently or skip roster rows at load time. |
| **Treat IDS IDs like weak credentials.** | Anyone knowing a Client/Doula ID can reach their respective flows on an unlocked unattended terminal. Lock screens; log off shared PCs. |
| **Do not run untrusted forks** of the script from email attachments **without reviewing code** with IDS’s trusted vendor. | Supply-chain integrity for billing software protects families and IDS financially. |
| **Confirm `IDS-Rates.txt`** after edits (spot-check one invoice). | Incorrect numeric keys (`tele_base`, hourly rates, mileage cents) propagate to every invoice. |
| **`invoice_<ClientID>.txt` disclosure** contains **billing PII.** | Store/send only via IDS-approved confidentiality channels consistent with HIPAA or state privacy norms if applicable—this document does not constitute legal counsel. |
| **Single-writer expectation** — avoid two people editing **the same roster file concurrently** via unsynchronized cloud sync. | Concurrent writes can silently merge badly; designate one authoritative editor session. |

When in doubt—**preserve backup copies** and reproduce the issue against `python IDS_Invoice_Application.py --demo` before overwriting production data files.

---

*This document fulfills IDS-Requirements.md: Maintenance and Support.*

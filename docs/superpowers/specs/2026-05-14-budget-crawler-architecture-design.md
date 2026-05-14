# budget-crawler: All-India Budget Acquisition System — Architecture Design

**Date:** 2026-05-14
**Status:** Approved
**First use case:** ICDS/Anganwadi Services funding, centre + state

---

## Purpose

A general all-India budget acquisition and extraction pipeline. Scrapers download raw budget documents from central and state government sources; an extraction layer reads those documents and writes scheme-level fiscal data into a queryable SQLite database. ICDS funding (central transfers via MWCD + state WCD department expenditures) is the first extraction target.

---

## Architecture

Two layers. Raw files are the ground truth; the extraction layer is re-runnable without re-downloading.

```
LAYER 1: ACQUISITION
  union_budget_scraper.py          ──┐
  state_budget_scrapers.py         ──┼──► budget_docs (SQLite index)
  scripts/download_openbudgets_india.py  ──┘    raw files on disk (data/)

LAYER 2: EXTRACTION
  extract_scheme_data.py
    reads budget_docs → routes by file type →
    writes to scheme_allocations

OUTPUT: queryable SQLite (db/budget_metadata.db)
  scheme_allocations  — query by scheme, state, year, level
  scheme_expenditures — phase 2 (controller-general monthly accounts)
```

`budget_docs` already exists. `scheme_allocations` and `scheme_expenditures` are new tables added in this work.

---

## Data Sources

Three acquisition channels, in priority order:

### 1. Union Budget (`union_budget_scraper.py` — new)

- **URL pattern:** `https://www.indiabudget.gov.in/doc/eb/sbe{demand}.xlsx`
- **MVP target:** Demand 101 (Ministry of Women and Child Development)
- **Format:** XLS, clean, direct pandas read — no PDF routing needed
- **Columns per scheme line:** Actuals (n-2), BE (n-1), RE (n-1), BE (n) — four values, three years of data per file
- **Historical coverage:** ~2010 onwards
- **Accessibility:** confirmed reachable from this machine (HTTP 200)
- **Key scheme for ICDS:** Scheme line 10 within Demand 101 — "Saksham Anganwadi and POSHAN 2.0" (covers Anganwadi Services, POSHAN Abhiyan, Scheme for Adolescent Girls). Prior names: "Umbrella ICDS" (2017–2021), "ICDS" (pre-2017). All map to canonical slug `icds_anganwadi_services`.

### 2. State portal scrapers (`state_budget_scrapers.py` — extend existing)

**Already implemented:** Assam, Tamil Nadu, Kerala, Uttar Pradesh, Rajasthan, Madhya Pradesh

**MVP priority states for ICDS** (large spend, data availability, political contrast):

| State | Scraper status | Rationale |
|---|---|---|
| Rajasthan | ✓ exists | Large tribal population, high ICDS dependence |
| Uttar Pradesh | ✓ exists | Largest state by ICDS beneficiary count |
| Madhya Pradesh | ✓ exists | High malnutrition burden |
| Maharashtra | ✗ needs new entry | Large budget, strong data publication |
| West Bengal | ✗ needs new entry | High ICDS coverage historically |

Target document per state: WCD department demand for grants PDF, annual.

**Eventually (phase 2):** remaining 19 states + 8 UTs — add registry entries as portals are confirmed accessible.

### 3. OBI/CKAN (`scripts/download_openbudgets_india.py` — already exists)

- Blocked from cloud IPs (Cloudflare); run locally to fill coverage gaps
- Used as fallback where state portals are unreliable or inaccessible
- Query: `package_search?q=women+child+development&rows=50`

---

## Database Schema

### `budget_docs` (existing — no changes)

```sql
-- id, state, fiscal_year, local_path, file_extension, url, ...
```

### `scheme_allocations` (new)

```sql
CREATE TABLE IF NOT EXISTS scheme_allocations (
    id               TEXT PRIMARY KEY,   -- sha256(doc_id + scheme_canonical + fiscal_year + col_type)
    doc_id           TEXT REFERENCES budget_docs(id),
    level            TEXT NOT NULL,      -- 'central' | 'state'
    state            TEXT,               -- NULL for central
    fiscal_year      TEXT NOT NULL,      -- '2024-25'
    demand_no        TEXT,               -- '101' for MWCD
    scheme_name      TEXT NOT NULL,      -- verbatim from source
    scheme_canonical TEXT NOT NULL,      -- controlled slug: 'icds_anganwadi_services'
    col_type         TEXT NOT NULL,      -- 'actual' | 'be' | 're'
    revenue_cr       REAL,
    capital_cr       REAL,
    total_cr         REAL,
    extracted_at     TEXT NOT NULL
);
```

### `scheme_expenditures` (new, empty in MVP)

Same structure as `scheme_allocations`. Populated in phase 2 from Controller General of Accounts monthly expenditure statements. Reserved now so queries can join allocations and actuals in the same table structure.

### `scheme_canonical_map` (new)

```sql
CREATE TABLE IF NOT EXISTS scheme_canonical_map (
    source_name      TEXT PRIMARY KEY,   -- verbatim name as it appears in source
    canonical        TEXT NOT NULL,      -- stable slug
    level            TEXT,               -- 'central' | 'state' | NULL (both)
    notes            TEXT
);
```

Seed rows for ICDS:

| source_name | canonical |
|---|---|
| Integrated Child Development Services | icds_anganwadi_services |
| Umbrella ICDS | icds_anganwadi_services |
| Anganwadi Services | icds_anganwadi_services |
| Saksham Anganwadi and POSHAN 2.0 | icds_anganwadi_services |
| ICDS | icds_anganwadi_services |

---

## Extraction Layer

`extract_scheme_data.py` runs as a separate pass over `budget_docs`. It reads unextracted documents, routes by file type, and writes to `scheme_allocations`.

### Routing

```
file_extension == xls/xlsx  →  xls_extractor (pandas)
parser_route == text_pdf    →  text_pdf_extractor (pdftotext + regex)
parser_route == table_pdf   →  table_pdf_extractor (pdfplumber)
parser_route == scanned_pdf →  ocr_extractor (tesseract subprocess)
parser_route == devanagari_pdf → flag for manual review
```

`parser_route` is already set by `analyze_docs.py` in `doc_extraction_probe`. No re-routing needed.

### Union Budget XLS extraction

Column positions are stable across years: Actuals | BE | RE | BE in columns C–N. Parse all scheme lines under "TRANSFERS TO STATES/UTs → Centrally Sponsored Schemes". Match scheme names against `scheme_canonical_map`; write one row per (scheme, year, col_type).

### State PDF extraction

1. Open PDF, find the WCD department demand section (search for "Women and Child Development" or "महिला एवं बाल विकास" header)
2. Extract tables on pages following that header
3. Match scheme lines containing "Anganwadi", "ICDS", "POSHAN", or "Child Development" against `scheme_canonical_map`
4. Write rows to `scheme_allocations` with `level='state'`

### Idempotency

Before writing any row, check: `SELECT 1 FROM scheme_allocations WHERE id = ?`. Skip if present. All runs are safe to repeat.

---

## MVP Delivery Scope

**Phase 1 — delivers a queryable ICDS dataset:**

1. `union_budget_scraper.py` — scrape Demand 101 MWCD for all available years
2. `metadata.py` — add `scheme_allocations`, `scheme_expenditures`, `scheme_canonical_map` tables
3. `extract_scheme_data.py` — XLS extractor for Union Budget + PDF extractor for state WCD demands
4. Maharashtra and West Bengal registry entries in `state_budget_scrapers.py`
5. Seed `scheme_canonical_map` with ICDS name variants
6. Tests: XLS extraction produces correct rows; canonical mapping resolves all name variants; idempotency holds

**Phase 2 — all-India expansion:**
- Add remaining state registry entries (19 states + 8 UTs)
- Add CGA monthly expenditure scraper → `scheme_expenditures`
- Hindi/Devanagari PDF extraction for states that publish in Hindi

---

## What Is Not Built

- No Airflow/Prefect — pipeline runs are `make` targets, event-driven (annual budget publication). Orchestration overhead not justified for annual cadence.
- No API layer — direct SQLite queries are the interface.
- No real-time data — this is a batch acquisition system updated annually.
- No camelot-py — requires Java; pdfplumber handles table PDFs.

---

## Open Questions

1. **Maharashtra state portal URL** — needs manual verification before scraper entry is written.
2. **West Bengal portal URL** — same.
3. **OBI coverage for state WCD demands** — needs local CKAN query to determine which states OBI already has, to avoid building scrapers for states where OBI covers us.

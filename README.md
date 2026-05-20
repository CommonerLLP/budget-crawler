# budget-crawler

Automated acquisition of Indian public finance data — Union Government and state budgets — with structured output for fiscal research.

**Status: `v0.1.0` — alpha. Three sources work reliably. State coverage is early. See [ROADMAP.md](ROADMAP.md) for what is planned.**

---

## What works

| Source | Script | Coverage | Output |
|---|---|---|---|
| RBI State Finances | `rbi_budgets_scraper.py` | 5 years (2021–2025 publications), all appendices, all-India | PDF + XLS in `data/rbi/` |
| Union Budget SBE | `union_budget_scraper.py` | 7 years (2020-21 to 2026-27), Demand No. 101 (MWCD) | XLS in `data/union_budget/` |
| Rajasthan | `state_budget_scrapers.py` | 2025-26, full document set | PDF in `data/state_budgets/Rajasthan/` |

## What is partially working

| Source | Script | Issue |
|---|---|---|
| Uttar Pradesh | `state_budget_scrapers.py` | Only 3 of 6 document sections; only current year pulled |
| Gujarat | `gujarat_scraper.py` | Wrong source — CMO press PDFs, not Finance Dept grant data |
| Kerala | `state_budget_scrapers.py` | Dynamic portal; known-sample mode not yet executed |
| Assam | `state_budget_scrapers.py` | Scraper written for 2017-18 only; not run |

## What is not working

| Source | Issue |
|---|---|
| Tamil Nadu | JS-rendered portal; static XPATH fails silently |
| Madhya Pradesh | `finance.mp.gov.in` timed out during scouting; placeholder only |
| 29 other states/UTs | No scraper exists |

---

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python budget_crawler/db_init.py
```

### RBI State Finances

```bash
# Preview without downloading
python budget_crawler/rbi_budgets_scraper.py --dry-run

# Download current publication
python budget_crawler/rbi_budgets_scraper.py

# Download a specific archived year (pass the RBI publication page URL)
python budget_crawler/rbi_budgets_scraper.py --url <url> --fiscal-year 2023-24
```

### Union Budget Demand for Grants

```bash
# Download all archive years for a demand number
python budget_crawler/union_budget_scraper.py --demand 101 --out data/union_budget

# Dry run
python budget_crawler/union_budget_scraper.py --demand 101 --dry-run
```

### State budget scrapers

```bash
# Rajasthan 2025-26 (works)
python budget_crawler/state_budget_scrapers.py rajasthan --fiscal-year 2025-26

# Uttar Pradesh 2026-27 (partial)
python budget_crawler/state_budget_scrapers.py uttar-pradesh --fiscal-year 2026-27

# Kerala known sample (4 documents, works)
python budget_crawler/state_budget_scrapers.py kerala --fiscal-year 2025-26 --known-sample

# Dry-run any state before downloading
python budget_crawler/state_budget_scrapers.py <state> --fiscal-year <year> --dry-run
```

Available state choices: `assam`, `tamil-nadu`, `kerala`, `uttar-pradesh`, `rajasthan`, `madhya-pradesh`

---

## Data layout

```
data/                         # gitignored — lives on external volume or local disk
  rbi/                        # RBI State Finances publications
  union_budget/               # Union Budget SBE XLS files
  state_budgets/              # State Finance Dept documents
  min_wage/                   # State Labour Dept minimum wage schedules
db/
  budget_metadata.db          # SQLite index of all downloaded documents (gitignored)
```

---

## Notes

- `cbga_parsers/` and `cbga_scrapers/` are upstream CBGA reference clones kept locally. They are gitignored and not vendored.
- Per-host sleep is set in `scrapping_utils.py`. Do not remove it.
- Never commit `data/`, `db/`, or `notes/` — they are gitignored for a reason.
- See [ROADMAP.md](ROADMAP.md) for version milestones and known gaps.

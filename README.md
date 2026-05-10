# Budget Crawler

Standalone crawler workspace for Indian budget documents and fiscal tables.

## Current Contents

- `budget_crawler/`: local scraper and extraction scripts for RBI and Gujarat budget sources.
- `data/`: downloaded PDFs/XLS files. Generated output; ignored by git.
- `db/budget_metadata.db`: local SQLite metadata index. Generated output; ignored by git.
- `cbga_parsers/` and `cbga_scrapers/`: upstream CBGA reference repositories kept as local references.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python budget_crawler/db_init.py
```

## Crawlers

Preview the live RBI State Finances publication without downloading:

```bash
python budget_crawler/rbi_budgets_scraper.py --dry-run
```

Download/index the current RBI publication:

```bash
python budget_crawler/rbi_budgets_scraper.py
```

If you have a compatible archived RBI annual-publication page, pass it with `--url` and use
`--fiscal-year` to override the inferred year.

Download/index the known Gujarat CMO budget ebooks:

```bash
python budget_crawler/gujarat_cmo_scraper.py
```

## CBGA-derived state scrapers

Assam and Tamil Nadu scraper ports live in `budget_crawler/state_budget_scrapers.py`.
They keep CBGA's state-specific discovery strategy, but add dry-runs, safer paths,
and metadata indexing.

Preview Assam's 2017-18 finance document collection:

```bash
python3 budget_crawler/state_budget_scrapers.py assam --fiscal-year 2017-18 --dry-run
```

Preview Tamil Nadu's current demand/publication page:

```bash
python3 budget_crawler/state_budget_scrapers.py tamil-nadu --fiscal-year 2025-26 --dry-run
```

For the older CBGA Tamil Nadu menu layout, use:

```bash
python3 budget_crawler/state_budget_scrapers.py tamil-nadu --fiscal-year 2017-18 --legacy --dry-run
```

Remove `--dry-run` to download and index files. Use `--limit N` for small reproduction runs.
If a government listing page is unreachable, use `--known-sample` to print or
download a small documented source sample:

```bash
python3 budget_crawler/state_budget_scrapers.py assam --fiscal-year 2017-18 --known-sample --dry-run
python3 budget_crawler/state_budget_scrapers.py tamil-nadu --fiscal-year 2025-26 --known-sample --dry-run
```

Additional state scouts:

```bash
python3 budget_crawler/state_budget_scrapers.py kerala --fiscal-year 2025-26 --known-sample --dry-run
python3 budget_crawler/state_budget_scrapers.py uttar-pradesh --fiscal-year 2026-27 --dry-run
python3 budget_crawler/state_budget_scrapers.py rajasthan --fiscal-year 2025-26 --dry-run
python3 budget_crawler/state_budget_scrapers.py madhya-pradesh --fiscal-year 2025-26 --dry-run
```

The current SQLite index was migrated out of the Sansad repo with the harvested data. Before committing code, keep generated data and local virtual environments out of git.

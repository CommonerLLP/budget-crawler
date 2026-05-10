# budget-crawler — common operations.
# `make help` lists everything.

VENV   := .venv
PYTHON := $(VENV)/bin/python

$(PYTHON):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

.PHONY: test sync-agents audit clean help

test: $(PYTHON)
	$(PYTHON) -m pytest tests/ -v

sync-agents: $(PYTHON)
	$(PYTHON) scripts/sync_agents.py

audit: $(PYTHON)
	$(VENV)/bin/pip-audit || true

clean:
	find . -name __pycache__ -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

help:
	@echo "budget-crawler operations:"
	@echo "  make test          — run pytest tests/ (write tests as you implement scrapers)"
	@echo "  make sync-agents   — regenerate CLAUDE.md + AGENTS.md from CONTEXT.md"
	@echo "  make audit         — run pip-audit on dependencies"
	@echo "  make clean         — drop __pycache__ and .pyc files"

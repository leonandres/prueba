PYTHON?=python3
VENV?=.venv
ACTIVATE=. $(VENV)/bin/activate;

.PHONY: install run worker lint sample

install:
$(PYTHON) -m venv $(VENV)
$(ACTIVATE) pip install --upgrade pip
$(ACTIVATE) pip install -r backend/requirements.txt

run:
$(ACTIVATE) uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

sample:
@echo "Sample dataset located at backend/data/sample_dataset.csv"

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List


class Ingestor:
    """Read CSV data from a given path."""

    def load(self, path: Path) -> List[dict]:
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def normalize(self, rows: Iterable[dict]) -> List[dict]:
        normalized = []
        for row in rows:
            normalized.append({k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()})
        return normalized


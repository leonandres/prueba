from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Sequence


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]


class Validator:
    EXPECTED_FIELDS = {"id", "customer", "amount", "category", "timestamp"}
    ALLOWED_CATEGORIES = {"retail", "wholesale", "services", "other"}

    def validate_schema(self, rows: Sequence[dict]) -> ValidationResult:
        errors: List[str] = []
        for idx, row in enumerate(rows, start=1):
            missing = self.EXPECTED_FIELDS - set(row.keys())
            if missing:
                errors.append(f"Row {idx}: missing fields {sorted(missing)}")
        return ValidationResult(valid=not errors, errors=errors)

    def validate_business(self, rows: Sequence[dict]) -> ValidationResult:
        errors: List[str] = []
        for idx, row in enumerate(rows, start=1):
            try:
                amount = float(row.get("amount", 0))
            except (ValueError, TypeError):
                errors.append(f"Row {idx}: amount must be numeric")
                continue

            if amount <= 0:
                errors.append(f"Row {idx}: amount must be positive")

            category = row.get("category")
            if category not in self.ALLOWED_CATEGORIES:
                errors.append(f"Row {idx}: category '{category}' is not allowed")

            timestamp = row.get("timestamp")
            try:
                datetime.fromisoformat(timestamp)
            except Exception:
                errors.append(f"Row {idx}: timestamp '{timestamp}' is not ISO format")
        return ValidationResult(valid=not errors, errors=errors)


from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List


class Metrics:
    def compute(self, rows: List[dict]) -> Dict:
        totals = 0.0
        per_category = defaultdict(float)
        customers = Counter()
        for row in rows:
            amount = float(row.get("amount", 0))
            totals += amount
            per_category[row["category"]] += amount
            customers[row["customer"]] += 1
        average_ticket = totals / len(rows) if rows else 0
        return {
            "rows": len(rows),
            "amount_total": round(totals, 2),
            "per_category": {k: round(v, 2) for k, v in per_category.items()},
            "top_customers": customers.most_common(5),
            "average_ticket": round(average_ticket, 2),
        }


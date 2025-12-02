from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from fpdf import FPDF
from jinja2 import Environment, FileSystemLoader, select_autoescape


class Renderer:
    def __init__(self, template_dir: Path):
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"]))

    def render_html(self, rows: List[dict], metrics: Dict) -> str:
        template = self.env.get_template("report.html")
        return template.render(rows=rows, metrics=metrics)

    def render_pdf(self, html: str, metrics: Dict, output_path: Path) -> Path:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt="ETL Report")
        pdf.ln()
        pdf.multi_cell(0, 8, txt=f"Rows: {metrics.get('rows', 0)}")
        pdf.multi_cell(0, 8, txt=f"Total amount: {metrics.get('amount_total', 0)}")
        pdf.multi_cell(0, 8, txt=f"Average ticket: {metrics.get('average_ticket', 0)}")
        pdf.ln()
        pdf.multi_cell(0, 8, txt="Top customers:")
        for customer, count in metrics.get("top_customers", []):
            pdf.multi_cell(0, 6, txt=f"- {customer}: {count} orders")
        pdf.output(str(output_path))
        return output_path


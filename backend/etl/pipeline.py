from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .ingest import Ingestor
from .metrics import Metrics
from .render import Renderer
from .validate import Validator


@dataclass
class PipelineConfig:
    template_dir: Path


class ETLPipeline:
    def __init__(self, config: PipelineConfig):
        self.ingestor = Ingestor()
        self.validator = Validator()
        self.metrics = Metrics()
        self.renderer = Renderer(config.template_dir)

    def run(self, input_path: Path, output_dir: Path) -> Dict:
        rows = self.ingestor.normalize(self.ingestor.load(input_path))
        schema_result = self.validator.validate_schema(rows)
        business_result = self.validator.validate_business(rows)

        errors = schema_result.errors + business_result.errors
        if errors:
            raise ValueError("; ".join(errors))

        metrics = self.metrics.compute(rows)
        html = self.renderer.render_html(rows, metrics)
        preview_path = output_dir / f"{input_path.stem}_preview.html"
        preview_path.write_text(html)
        pdf_path = output_dir / f"{input_path.stem}_report.pdf"
        self.renderer.render_pdf(html, metrics, pdf_path)

        return {
            "metrics": metrics,
            "preview_html": preview_path,
            "pdf": pdf_path,
        }


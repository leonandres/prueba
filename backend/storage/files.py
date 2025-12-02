from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class StorageConfig:
    base_path: Path
    uploads_path: Path
    reports_path: Path


class FileStorage:
    def __init__(self, config: StorageConfig):
        self.base_path = Path(config.base_path)
        self.uploads_path = Path(config.uploads_path)
        self.reports_path = Path(config.reports_path)

    def ensure_folders(self):
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.uploads_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content: bytes) -> Path:
        self.ensure_folders()
        path = self.uploads_path / filename
        path.write_bytes(content)
        return path

    def copy_to_reports(self, source: Path, name: Optional[str] = None) -> Path:
        self.ensure_folders()
        target_name = name or source.name
        target = self.reports_path / target_name
        shutil.copy(source, target)
        return target

    def exists(self, path: str) -> bool:
        return Path(path).exists()


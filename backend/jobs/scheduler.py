from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import Optional

from croniter import croniter

from etl.pipeline import ETLPipeline
from storage.files import FileStorage
from .store import JobRecord, JobStatus, JobStore


class JobScheduler:
    def __init__(self, store: JobStore, pipeline: ETLPipeline, storage: FileStorage, max_retries: int = 2):
        self.store = store
        self.pipeline = pipeline
        self.storage = storage
        self.max_retries = max_retries
        self.queue: Queue[JobRecord] = Queue()
        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._cron_thread: Optional[threading.Thread] = None
        self.cron_expression = "0 * * * *"  # hourly
        self.cron_input = None

    def start(self):
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()
        self._cron_thread = threading.Thread(target=self._run_cron, daemon=True)
        self._cron_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._worker:
            self._worker.join(timeout=1)
        if self._cron_thread:
            self._cron_thread.join(timeout=1)

    def enqueue(self, input_path: str, description: Optional[str] = None) -> str:
        job_id = str(uuid.uuid4())
        record = JobRecord(
            id=job_id,
            input_path=input_path,
            description=description,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.store.create(record)
        self.queue.put(record)
        return job_id

    def schedule_cron(self, cron_expression: str, input_path: str, description: Optional[str] = None):
        self.cron_expression = cron_expression
        self.cron_input = (input_path, description)

    def _run_cron(self):
        while not self._stop_event.is_set():
            if not self.cron_input:
                time.sleep(5)
                continue
            now = datetime.now()
            iterator = croniter(self.cron_expression, now)
            next_run = iterator.get_next(datetime)
            sleep_for = (next_run - now).total_seconds()
            if sleep_for > 0:
                time.sleep(min(sleep_for, 5))
                continue
            self.enqueue(*self.cron_input)
            time.sleep(60)

    def _run_worker(self):
        while not self._stop_event.is_set():
            try:
                record: JobRecord = self.queue.get(timeout=1)
            except Empty:
                continue
            self._process(record)
            self.queue.task_done()

    def _process(self, record: JobRecord):
        record.status = JobStatus.RUNNING
        record.updated_at = datetime.utcnow()
        self.store.update(record)
        try:
            output_dir = Path(self.storage.reports_path)
            result = self.pipeline.run(Path(record.input_path), output_dir)
            record.status = JobStatus.SUCCESS
            record.output_pdf = str(result["pdf"])
            record.preview_html = str(result["preview_html"])
            record.metrics = result["metrics"]
            record.updated_at = datetime.utcnow()
            self.store.update(record)
        except Exception as exc:  # noqa: BLE001
            record.attempts += 1
            record.error = str(exc)
            if record.attempts <= self.max_retries:
                record.status = JobStatus.RETRY
                record.updated_at = datetime.utcnow()
                self.store.update(record)
                self.queue.put(record)
            else:
                record.status = JobStatus.FAILED
                record.updated_at = datetime.utcnow()
                self.store.update(record)


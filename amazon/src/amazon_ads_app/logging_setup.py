"""Structured logging with rotating file handler."""

from __future__ import annotations

import json
import logging
import logging.handlers
from pathlib import Path
from typing import Any


class JsonLineFormatter(logging.Formatter):
    """One JSON object per line for machine-readable logs."""

    _reserved = frozenset(
        {
            "name",
            "msg",
            "args",
            "taskName",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        base: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k in self._reserved or k.startswith("_"):
                continue
            base[k] = v
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, default=str)


def setup_logging(log_dir: Path, *, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    fh = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(JsonLineFormatter())

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(JsonLineFormatter())

    root.addHandler(fh)
    root.addHandler(ch)

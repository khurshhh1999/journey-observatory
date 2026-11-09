"""Write a failure record the DAG callback can drop on disk. No remote alert."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def write_failure(context: dict, directory: Path | None = None) -> Path:
    target = directory or Path(os.environ.get("OBSERVATORY_ALERT_DIR", "airflow/alerts"))
    target.mkdir(parents=True, exist_ok=True)
    task = context.get("task_instance")
    payload = {
        "dag": getattr(context.get("dag"), "dag_id", None),
        "task": getattr(task, "task_id", None),
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exception": str(context.get("exception") or ""),
    }
    path = target / "failure.json"
    path.write_text(json.dumps(payload, indent=2))
    return path

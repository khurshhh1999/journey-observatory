from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY_PATHS = [
    ROOT / "README.md",
    ROOT / "web" / "README.md",
    ROOT / "docs",
    ROOT / "web" / "src" / "content",
]
TEXT_ROOTS = [
    ROOT / "web" / "src" / "app",
    ROOT / "web" / "src" / "views",
    ROOT / "web" / "src" / "components" / "shell.tsx",
]


def _strip_allowed(text: str) -> str:
    text = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b", "", text)
    text = re.sub(r"\bv?\d+\.\d+\.\d+\b", "", text)
    return text


def _copy_files() -> list[Path]:
    files: list[Path] = []
    for path in COPY_PATHS:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(path.rglob("*.md"))
            files.extend(path.rglob("*.ts"))
            files.extend(path.rglob("*.tsx"))
    return files


def test_customer_copy_has_no_metric_digits():
    failures: list[str] = []
    metric = re.compile(
        r"\$\s*\d|\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*[MmKk]\+|\d+(?:\.\d+)?\s+million",
        re.I,
    )
    for path in _copy_files():
        cleaned = _strip_allowed(path.read_text())
        if re.search(r"\d", cleaned):
            failures.append(str(path.relative_to(ROOT)))
    for path in TEXT_ROOTS:
        candidates = [path] if path.is_file() else list(path.rglob("*.tsx")) if path.exists() else []
        for candidate in candidates:
            text = candidate.read_text()
            for node in re.findall(r">([^<{}\n]*\d[^<{}\n]*)<", text):
                if metric.search(node):
                    failures.append(f"{candidate.relative_to(ROOT)}: {node.strip()}")
            for literal in re.findall(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'', text):
                blob = "".join(literal)
                if metric.search(blob):
                    failures.append(f"{candidate.relative_to(ROOT)}: {blob}")
    assert not failures, "Metric-like digits in customer copy:\n" + "\n".join(failures)

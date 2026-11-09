"""Run the local pipeline from generate through export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.config import ROOT, Config, load_config
from pipeline.proforma import ScenarioResult
from pipeline.steps import ORDER, _connect, _high_rows, step


@dataclass(frozen=True)
class RunResult:
    rows: int
    events: int
    high_variants: tuple[str, ...]
    scenarios: dict[str, ScenarioResult]
    sensitivity: list[dict]
    quality: dict


def run(config: Config | None = None, *, write_site: bool = True, root: Path = ROOT) -> RunResult:
    config = config or load_config()
    for name in ORDER:
        step(name, root=root, config=config, write_site=write_site)
    return _read_result(root, config)


def _read_result(root: Path, config: Config) -> RunResult:
    from pipeline.proforma import price_variants, sensitivity
    from pipeline.quality import assert_population

    con = _connect(root)
    quality = assert_population(con, config, int(con.execute("SELECT count(*) FROM population_audit").fetchone()[0]))
    rows = _high_rows(con)
    scenarios = {name: price_variants(rows, config, scales) for name, scales in config.scenarios.items()}
    shocks = sensitivity(rows, config)
    con.close()
    return RunResult(
        rows=quality["rows"],
        events=quality["events"],
        high_variants=tuple(row["variant"] for row in rows),
        scenarios=scenarios,
        sensitivity=shocks,
        quality=quality,
    )


if __name__ == "__main__":
    result = run()
    base = result.scenarios["base"]
    print(f"rows={result.rows}")
    print(f"events={result.events}")
    print(f"high={','.join(result.high_variants)}")
    print(f"modeled_cents={base.modeled_cents}")
    print(f"contact_reduction={base.contact_reduction}")

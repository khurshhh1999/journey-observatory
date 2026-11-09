"""Idempotent pipeline steps. Each one overwrites its own outputs."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from data_gen.catalog import CASE_INPUT_COLUMNS
from data_gen.population import build_population
from pipeline.config import ROOT, Config, load_config
from pipeline.export import write_outputs
from pipeline.proforma import price_variants, sensitivity
from pipeline.quality import assert_population
from pipeline.sql_runner import run_sql

ORDER = ("generate", "stage", "link", "friction", "quality", "model", "export")


def warehouse(root: Path) -> Path:
    path = root / "data" / "warehouse"
    path.mkdir(parents=True, exist_ok=True)
    return path


def step(name: str, *, root: Path | None = None, config: Config | None = None, write_site: bool = True) -> None:
    root = root or Path(os.environ.get("OBSERVATORY_ROOT", ROOT))
    config = config or load_config()
    if name == "generate":
        _generate(root, config)
    elif name == "stage":
        _stage(root)
    elif name == "link":
        _link(root)
    elif name == "friction":
        _friction(root, config)
    elif name == "quality":
        _quality(root, config)
    elif name == "model":
        _model(root, config)
    elif name == "export":
        _export(root, config, write_site)
    else:
        raise ValueError(name)


def _generate(root: Path, config: Config) -> None:
    population = build_population(config)
    pq.write_table(population, warehouse(root) / "features.parquet")


def _stage(root: Path) -> None:
    frame = pq.read_table(warehouse(root) / "features.parquet")
    con = duckdb.connect(str(warehouse(root) / "observatory.duckdb"))
    con.register("population", frame)
    columns = ", ".join(CASE_INPUT_COLUMNS)
    con.execute(f"CREATE OR REPLACE TABLE case_input AS SELECT {columns} FROM population")
    con.execute("CREATE OR REPLACE TABLE population_audit AS SELECT reservation_id, planted_pattern FROM population")
    con.close()


def _link(root: Path) -> None:
    con = _connect(root)
    run_sql(con, "03_classify.sql")
    mismatches = con.execute(
        """
        SELECT a.planted_pattern, c.variant, count(*)
        FROM classified c
        JOIN population_audit a USING (reservation_id)
        WHERE c.variant != a.planted_pattern
        GROUP BY 1, 2
        ORDER BY 3 DESC
        LIMIT 12
        """
    ).fetchall()
    con.close()
    if mismatches:
        raise RuntimeError(f"Classification did not recover the planted journeys: {mismatches}")


def _friction(root: Path, config: Config) -> None:
    con = _connect(root)
    run_sql(con, "04_friction.sql", gap_ratio=float(config.gap_ratio))
    con.close()


def _quality(root: Path, config: Config) -> None:
    con = _connect(root)
    expected = con.execute("SELECT count(*) FROM population_audit").fetchone()[0]
    assert_population(con, config, int(expected))
    con.close()


def _model(root: Path, config: Config) -> None:
    # The model is pure and reads the friction table. Export persists it.
    # Running it here proves the gate has already passed and the table is ready.
    con = _connect(root)
    rows = _high_rows(con)
    if not rows:
        con.close()
        raise RuntimeError("The friction step did not leave a high-friction group.")
    price_variants(rows, config, config.scenarios["base"])
    con.close()


def _export(root: Path, config: Config, write_site: bool) -> None:
    frame = pq.read_table(warehouse(root) / "features.parquet")
    con = _connect(root)
    rows = _high_rows(con)
    scenarios = {
        name: price_variants(rows, config, scales)
        for name, scales in config.scenarios.items()
    }
    sensitivity(rows, config)
    write_outputs(
        con,
        frame,
        config,
        scenarios,
        export_dir=root / "exports",
        site_dir=(root / "web" / "src" / "data") if write_site else None,
    )
    con.close()


def _connect(root: Path) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(warehouse(root) / "observatory.duckdb"))


def _high_rows(con: duckdb.DuckDBPyConnection) -> list[dict]:
    found = con.execute(
        """
        SELECT variant, cases, dropoff_cases, contacts, dropoff_value_cents
        FROM variant_stats
        WHERE high_friction = 1
        ORDER BY rank
        """
    ).fetchall()
    return [
        {
            "variant": variant,
            "cases": int(cases),
            "dropoff_cases": int(dropoff_cases),
            "contacts": int(contacts),
            "dropoff_value_cents": int(value),
        }
        for variant, cases, dropoff_cases, contacts, value in found
    ]

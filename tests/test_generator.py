from __future__ import annotations

import pyarrow as pa

from data_gen.expand import expand_row
from data_gen.population import build_population
from pipeline.config import load_config
from pipeline.sql_runner import run_sql


def test_population_is_deterministic():
    config = load_config()
    first = build_population(config)
    second = build_population(config)
    assert first.equals(second)


def test_expanded_events_match_the_recipe_counts():
    import duckdb

    config = load_config()
    population = build_population(config)
    con = duckdb.connect()
    con.register("population", population)
    sample = con.execute(
        """
        SELECT * EXCLUDE (n)
        FROM (
            SELECT *, row_number() OVER (PARTITION BY planted_pattern ORDER BY reservation_id) AS n
            FROM population
        )
        WHERE n = 1
        """
        ).to_arrow_table()
    assert sample.num_rows == 20
    for row in sample.to_pylist():
        events = [event for event in expand_row(row) if not event["duplicate"]]
        assert len(events) == int(row["n_raw_events"]) - int(row["n_duplicate_events"])

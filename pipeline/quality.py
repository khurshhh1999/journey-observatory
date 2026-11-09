"""Stop the model when the extract fails basic checks."""

from __future__ import annotations

import duckdb

from pipeline.config import Config


class DataQualityError(RuntimeError):
    pass


def assert_population(con: duckdb.DuckDBPyConnection, config: Config, expected_rows: int) -> dict:
    row = con.execute(
        """
        SELECT
            count(*) AS rows,
            coalesce(sum(n_raw_events), 0) AS events,
            coalesce(sum(n_duplicate_events), 0) AS duplicates,
            count(*) FILTER (WHERE reservation_id IS NULL) AS null_ids,
            count(*) FILTER (WHERE property_id IS NULL) AS null_properties,
            count(*) FILTER (WHERE n_search IS NULL) AS null_events
        FROM case_input
        """
    ).fetchone()
    rows, events, duplicates, null_ids, null_properties, null_events = row
    nulls = null_ids + null_properties + null_events
    duplicate_rate = (duplicates / events) if events else 1
    null_rate = (nulls / rows) if rows else 1
    report = {
        "rows": int(rows),
        "events": int(events),
        "duplicate_rate": float(duplicate_rate),
        "null_rate": float(null_rate),
    }
    if rows != expected_rows:
        raise DataQualityError(f"Row count {rows} does not match the population {expected_rows}.")
    if events < config.min_events:
        raise DataQualityError(f"Event volume {events} is below the configured floor.")
    if duplicate_rate > config.max_duplicate_rate:
        raise DataQualityError("Duplicate rate spiked above the gate.")
    if null_rate > config.max_null_rate:
        raise DataQualityError("Null rate spiked above the gate.")
    return report

from __future__ import annotations

import duckdb
import pyarrow as pa

from pipeline.sql_runner import run_sql


def _event(reservation_id, event_id, event_type, seq, time, amount=0, nights=2, value=40000):
    return {
        "event_id": event_id,
        "reservation_id": reservation_id,
        "guest_id": reservation_id,
        "property_id": 1,
        "event_type": event_type,
        "event_seq": seq,
        "event_time": time,
        "amount_cents": amount,
        "booking_value_cents": value,
        "nights": nights,
        "arrival_day": 10,
    }


def _classify(rows: list[dict]):
    con = duckdb.connect()
    con.register("raw_events", pa.Table.from_pylist(rows))
    run_sql(con, "01_stage.sql")
    run_sql(con, "02_aggregate.sql")
    run_sql(con, "03_classify.sql")
    return con


def test_duplicate_events_collapse_and_late_times_keep_sequence():
    rows = [
        _event(1, 1, "charge", 4, "2025-10-12T10:00:00", 15000),
        _event(1, 2, "charge", 4, "2025-10-12T10:05:00", 15000),
        _event(1, 3, "charge", 5, "2025-10-12T11:00:00", 22000),
        _event(2, 4, "search", 1, "2025-10-20T09:00:00"),
        _event(2, 5, "hold", 2, "2025-10-18T09:00:00"),
        _event(2, 6, "confirm", 3, "2025-10-19T09:00:00"),
    ]
    con = _classify(rows)
    charges = con.execute(
        "SELECT count(*) FROM linked_events WHERE reservation_id = 1 AND event_type = 'charge'"
    ).fetchone()[0]
    order = [
        row[0]
        for row in con.execute(
            "SELECT event_type FROM linked_events WHERE reservation_id = 2 ORDER BY process_order"
        ).fetchall()
    ]
    assert charges == 2
    assert order == ["search", "hold", "confirm"]


def test_missing_check_in_is_a_telemetry_gap_and_a_cancel_is_voluntary():
    rows = [
        _event(3, 1, "search", 1, "2025-10-01T09:00:00"),
        _event(3, 2, "quote", 2, "2025-10-01T10:00:00"),
        _event(3, 3, "hold", 3, "2025-10-01T11:00:00"),
        _event(3, 4, "confirm", 4, "2025-10-01T12:00:00"),
        _event(3, 5, "room_ready", 5, "2025-10-10T14:00:00"),
        _event(3, 6, "check_out", 6, "2025-10-12T11:00:00"),
        _event(4, 7, "search", 1, "2025-10-02T09:00:00"),
        _event(4, 8, "quote", 2, "2025-10-02T10:00:00"),
        _event(4, 9, "hold", 3, "2025-10-02T11:00:00"),
        _event(4, 10, "cancel", 4, "2025-10-03T11:00:00"),
    ]
    con = _classify(rows)
    labels = dict(con.execute("SELECT reservation_id, variant FROM classified ORDER BY 1").fetchall())
    assert labels[3] == "telemetry_gap"
    assert labels[4] == "voluntary_cancel"
    dropoff = dict(con.execute("SELECT reservation_id, dropoff FROM classified").fetchall())
    assert dropoff[3] == 0
    assert dropoff[4] == 0

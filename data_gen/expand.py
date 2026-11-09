"""Expand a reservation feature row into ordered raw events."""

from __future__ import annotations

from datetime import datetime, timedelta

import pyarrow as pa

from data_gen.catalog import EVENT_COUNT_COLUMNS, EVENT_LABELS

WINDOW_START = datetime(2025, 10, 1, 15, 0, 0)


def expand_table(table: pa.Table, *, cap_repeats: int | None = None) -> list[dict]:
    rows = table.to_pylist()
    events: list[dict] = []
    for row in rows:
        events.extend(expand_row(row, cap_repeats=cap_repeats))
    return events


def expand_row(row: dict, *, cap_repeats: int | None = None) -> list[dict]:
    arrival = WINDOW_START + timedelta(days=int(row["arrival_day"]))
    events: list[dict] = []
    seq = 1
    for column in EVENT_COUNT_COLUMNS:
        if column == "n_duplicate_events":
            continue
        event_type = column.removeprefix("n_")
        count = int(row[column])
        if cap_repeats is not None and event_type in {"folio", "charge"}:
            count = min(count, cap_repeats)
        for offset in range(count):
            amount = _amount(row, event_type, offset)
            events.append(
                _event(row, event_type, seq, arrival, amount, late=False, duplicate=False)
            )
            seq += 1
    if int(row.get("late_event", 0)) and events:
        confirm = next((event for event in events if event["type"] == "confirm"), events[0])
        confirm["late"] = True
        confirm["time"] = (
            datetime.fromisoformat(confirm["time"]) + timedelta(days=5)
        ).isoformat(timespec="minutes")
    if int(row.get("n_duplicate_events", 0)) and events:
        source = next((event for event in reversed(events) if event["type"] == "charge"), events[-1])
        copy = dict(source)
        copy["duplicate"] = True
        copy["event_id"] = int(row["reservation_id"]) * 1000 + 900
        copy["time"] = (
            datetime.fromisoformat(source["time"]) + timedelta(hours=2)
        ).isoformat(timespec="minutes")
        events.append(copy)
    return events


def _amount(row: dict, event_type: str, offset: int) -> int:
    if event_type != "charge":
        return 0
    base = max(int(row["booking_value_cents"]) // max(int(row["nights"]), 1), 1)
    # A planted duplicate pair shares one amount. Later charges differ.
    if int(row.get("n_duplicate_charge", 0)) and offset < 2:
        return base
    return base + offset


def _event(row: dict, event_type: str, seq: int, arrival: datetime, amount: int, *, late: bool, duplicate: bool) -> dict:
    when = arrival - timedelta(days=12) + timedelta(hours=3 * seq)
    return {
        "event_id": int(row["reservation_id"]) * 1000 + seq,
        "reservation_id": int(row["reservation_id"]),
        "guest_id": int(row["guest_id"]),
        "property_id": int(row["property_id"]),
        "type": event_type,
        "label": EVENT_LABELS.get(event_type, event_type),
        "seq": seq,
        "time": when.isoformat(timespec="minutes"),
        "amount_cents": amount,
        "late": late,
        "duplicate": duplicate,
    }

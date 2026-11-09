"""Build one deterministic reservation population and the event counts on it."""

from __future__ import annotations

import numpy as np
import pyarrow as pa

from data_gen.catalog import CASE_INPUT_COLUMNS, EVENT_COUNT_COLUMNS, PROPERTIES
from pipeline.config import Config


def build_population(config: Config) -> pa.Table:
    """Return every reservation. Event rows are counted here and expanded later."""
    quotas = _quotas(config)
    n = sum(spec["cases"] for spec in quotas.values())
    if n != sum(p.reservations for p in PROPERTIES):
        raise RuntimeError("Pattern quotas and property reservations do not match.")

    rng = np.random.default_rng(config.seed)
    property_id = np.repeat(
        np.array([p.id for p in PROPERTIES], dtype=np.int16),
        [p.reservations for p in PROPERTIES],
    )
    property_id = property_id[rng.permutation(n)]

    pattern = np.empty(n, dtype=object)
    dropoff = np.zeros(n, dtype=np.int8)
    cursor = 0
    for name, spec in quotas.items():
        count = spec["cases"]
        pattern[cursor : cursor + count] = name
        dropoff[cursor : cursor + spec["dropoff_cases"]] = 1
        cursor += count
    order = rng.permutation(n)
    pattern = pattern[order]
    dropoff = dropoff[order]

    reservation_id = np.arange(1, n + 1, dtype=np.int64)
    guest_id = (reservation_id * 17) % 900_000 + 1
    adr_lut = np.zeros(max(p.id for p in PROPERTIES) + 1, dtype=np.int32)
    nights_lut = np.zeros_like(adr_lut)
    for prop in PROPERTIES:
        adr_lut[prop.id] = prop.adr_cents
        nights_lut[prop.id] = prop.nights
    nights = nights_lut[property_id].astype(np.int16)
    booking_value_cents = adr_lut[property_id].astype(np.int64) * nights.astype(np.int64)
    arrival_day = (reservation_id % config.window_days).astype(np.int16)
    arrival_day = np.where(pattern == "censored", 87 + (reservation_id % 3), arrival_day).astype(np.int16)

    columns = _features(pattern, dropoff, nights, config)
    columns["n_duplicate_events"] = (reservation_id % 41 == 0).astype(np.int16)
    columns["n_raw_events"] = sum(columns[name].astype(np.int64) for name in EVENT_COUNT_COLUMNS)

    data: dict[str, np.ndarray] = {
        "reservation_id": reservation_id,
        "guest_id": guest_id.astype(np.int64),
        "property_id": property_id.astype(np.int16),
        "booking_value_cents": booking_value_cents,
        "nights": nights,
        "arrival_day": arrival_day,
        "planted_pattern": pattern.astype(str),
        "planted_dropoff": dropoff.astype(np.int8),
        "late_event": (reservation_id % 29 == 0).astype(np.int8),
    }
    data.update(columns)
    table = pa.table(data)
    missing = [name for name in CASE_INPUT_COLUMNS if name not in table.column_names]
    if missing:
        raise RuntimeError(f"Population is missing columns: {missing}")
    return table


def _quotas(config: Config) -> dict[str, dict]:
    quotas = {name: dict(spec) for name, spec in config.patterns.items()}
    special = sum(spec["cases"] for spec in quotas.values())
    total = sum(p.reservations for p in PROPERTIES)
    if special >= total:
        raise RuntimeError("Planted patterns use the whole population.")
    quotas = {
        "clean": {"cases": total - special, "dropoff_cases": 0, "label": "Completed stay"},
        **quotas,
    }
    return quotas


def _zeros(n: int) -> np.ndarray:
    return np.zeros(n, dtype=np.int16)


def _features(pattern: np.ndarray, dropoff: np.ndarray, nights: np.ndarray, config: Config) -> dict[str, np.ndarray]:
    n = pattern.size
    lost = dropoff == 1
    is_ = lambda name: pattern == name  # noqa: E731

    no_stay = (
        is_("voluntary_cancel")
        | is_("voluntary_noshow")
        | is_("policy_block")
        | (is_("payment_retry") & lost)
        | (is_("room_not_ready") & lost)
        | (is_("modification_loop") & lost)
        | (is_("hold_expired") & lost)
        | (is_("rate_reprice") & lost)
        | (is_("tender_mismatch") & lost)
    )
    stayed = ~no_stay

    cols = {name: _zeros(n) for name in (
        "n_search", "n_quote", "n_hold", "n_hold_expire", "n_confirm", "n_modify", "n_cancel",
        "n_policy_decline", "n_noshow", "n_payment_fail", "n_payment_retry", "n_payment_capture",
        "n_guarantee", "n_check_in", "n_room_ready", "n_room_wait", "n_folio", "n_check_out",
        "n_charge", "n_adjustment", "n_refund_request", "n_refund_post", "n_dispute_open",
        "n_dispute_close", "n_contact", "n_settle", "n_duplicate_charge", "n_late_checkout",
        "n_early_checkout", "n_key_reissue", "n_in_house",
    )}
    cols["n_search"][:] = 1
    cols["n_quote"][:] = 1
    cols["n_hold"][:] = 1
    cols["n_folio"] = np.where(stayed, nights.astype(np.int32) * config.folio_per_night, 0).astype(np.int16)
    cols["n_charge"] = np.where(stayed, nights.astype(np.int32) * config.charge_per_night, 0).astype(np.int16)

    def put(mask: np.ndarray, **values: int) -> None:
        for key, value in values.items():
            cols[key][mask] = value

    stay_ok = dict(n_confirm=1, n_check_in=1, n_room_ready=1, n_check_out=1, n_settle=1, n_payment_capture=1, n_guarantee=1)

    put(is_("clean"), **stay_ok)
    put(is_("voluntary_cancel"), n_cancel=1)
    put(is_("voluntary_noshow"), n_confirm=1, n_noshow=1)
    put(is_("policy_block"), n_policy_decline=1)
    put(is_("telemetry_gap"), n_confirm=1, n_guarantee=1, n_room_ready=1, n_check_out=1, n_payment_capture=1, n_settle=1)
    put(is_("censored"), n_confirm=1, n_check_in=1, n_room_ready=1, n_in_house=1, n_guarantee=1)
    put(is_("payment_retry"), n_payment_fail=2, n_payment_retry=2)
    put(is_("payment_retry") & lost, n_cancel=1)
    put(is_("payment_retry") & ~lost, **stay_ok)
    put(is_("room_not_ready"), n_confirm=1, n_check_in=1, n_room_wait=1, n_guarantee=1)
    put(is_("room_not_ready") & ~lost, n_room_ready=1, n_check_out=1, n_settle=1, n_payment_capture=1)
    put(is_("folio_dispute"), n_confirm=1, n_check_in=1, n_room_ready=1, n_check_out=1, n_dispute_open=1, n_guarantee=1, n_payment_capture=1)
    put(is_("folio_dispute") & ~lost, n_dispute_close=1, n_settle=1)
    put(is_("modification_loop"), n_modify=3)
    put(is_("modification_loop") & lost, n_cancel=1)
    put(is_("modification_loop") & ~lost, **stay_ok)
    put(is_("duplicate_charge"), n_confirm=1, n_check_in=1, n_room_ready=1, n_check_out=1, n_duplicate_charge=1, n_guarantee=1, n_payment_capture=1)
    put(is_("duplicate_charge") & ~lost, n_adjustment=1, n_settle=1)
    put(is_("refund_stall"), n_confirm=1, n_check_in=1, n_room_ready=1, n_check_out=1, n_refund_request=1, n_guarantee=1, n_payment_capture=1)
    put(is_("refund_stall") & ~lost, n_refund_post=1, n_settle=1)
    put(is_("hold_expired"), n_hold_expire=1)
    put(is_("hold_expired") & ~lost, **stay_ok)
    put(is_("rate_reprice"), n_adjustment=1, n_confirm=1, n_guarantee=1)
    put(is_("rate_reprice") & lost, n_cancel=1)
    put(is_("rate_reprice") & ~lost, n_check_in=1, n_room_ready=1, n_check_out=1, n_settle=1, n_payment_capture=1)
    put(is_("tender_mismatch"), n_confirm=1, n_payment_capture=1, n_payment_fail=1, n_payment_retry=1, n_guarantee=1)
    put(is_("tender_mismatch") & ~lost, n_check_in=1, n_room_ready=1, n_check_out=1, n_settle=1)
    put(is_("late_checkout"), n_confirm=1, n_check_in=1, n_room_ready=1, n_late_checkout=1, n_guarantee=1, n_payment_capture=1)
    put(is_("late_checkout") & ~lost, n_check_out=1, n_settle=1)
    put(is_("early_checkout"), n_confirm=1, n_check_in=1, n_room_ready=1, n_early_checkout=1, n_guarantee=1, n_payment_capture=1)
    put(is_("early_checkout") & ~lost, n_check_out=1, n_settle=1)
    put(is_("key_reissue"), n_confirm=1, n_check_in=1, n_room_ready=1, n_key_reissue=1, n_guarantee=1, n_payment_capture=1)
    put(is_("key_reissue") & ~lost, n_check_out=1, n_settle=1)
    put(is_("amenity_contact"), n_confirm=1, n_check_in=1, n_room_ready=1, n_guarantee=1, n_payment_capture=1)
    put(is_("amenity_contact") & ~lost, n_check_out=1, n_settle=1)
    put(is_("rate_absorbed"), n_confirm=1, n_check_in=1, n_room_ready=1, n_adjustment=1, n_guarantee=1, n_payment_capture=1)
    put(is_("rate_absorbed") & ~lost, n_check_out=1, n_settle=1)

    for name, spec in config.patterns.items():
        contacts = int(spec.get("contacts_per_case", 0))
        if contacts:
            cols["n_contact"][is_(name)] = contacts
    return cols

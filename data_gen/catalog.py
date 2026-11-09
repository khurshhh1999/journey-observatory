"""Fictional properties. Rates and lengths are generator inputs, not a performance claim."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Property:
    id: int
    code: str
    name: str
    market: str
    adr_cents: int
    nights: int
    reservations: int


PROPERTIES: tuple[Property, ...] = (
    Property(1, "HARBOR", "Harbor House", "Urban", 24500, 2, 120_000),
    Property(2, "KING", "King Street", "Urban", 31000, 2, 80_000),
    Property(3, "LINDEN", "Linden Court", "Urban", 18000, 3, 90_000),
    Property(4, "PIER", "Pier Terminal", "Airport", 16500, 1, 140_000),
    Property(5, "FIELD", "Field Station", "Airport", 14900, 1, 100_000),
    Property(6, "NORTH", "North Runway", "Airport", 18900, 2, 70_000),
    Property(7, "DUNE", "Dune House", "Resort", 42000, 3, 60_000),
    Property(8, "PALM", "Palm Court", "Resort", 51000, 4, 40_000),
    Property(9, "CEDAR", "Cedar Ridge", "Resort", 27500, 2, 50_000),
    Property(10, "MILL", "Mill Road", "Suburban", 14200, 2, 110_000),
    Property(11, "BROOK", "Brook Lane", "Suburban", 12800, 1, 80_000),
    Property(12, "WEST", "West Orchard", "Suburban", 16000, 3, 60_000),
)

# Population case_input columns. Classification reads these, never a planted label.
CASE_INPUT_COLUMNS: tuple[str, ...] = (
    "reservation_id",
    "guest_id",
    "property_id",
    "booking_value_cents",
    "nights",
    "arrival_day",
    "n_search",
    "n_quote",
    "n_hold",
    "n_hold_expire",
    "n_confirm",
    "n_modify",
    "n_cancel",
    "n_policy_decline",
    "n_noshow",
    "n_payment_fail",
    "n_payment_retry",
    "n_payment_capture",
    "n_guarantee",
    "n_check_in",
    "n_room_ready",
    "n_room_wait",
    "n_folio",
    "n_check_out",
    "n_charge",
    "n_adjustment",
    "n_refund_request",
    "n_refund_post",
    "n_dispute_open",
    "n_dispute_close",
    "n_contact",
    "n_settle",
    "n_duplicate_charge",
    "n_late_checkout",
    "n_early_checkout",
    "n_key_reissue",
    "n_in_house",
    "n_duplicate_events",
    "n_raw_events",
)

# Counts that become raw events. n_duplicate_charge is a pair marker already
# included inside n_charge, so it is not added again.
EVENT_COUNT_COLUMNS: tuple[str, ...] = (
    "n_search",
    "n_quote",
    "n_hold",
    "n_hold_expire",
    "n_payment_fail",
    "n_payment_retry",
    "n_payment_capture",
    "n_modify",
    "n_cancel",
    "n_confirm",
    "n_noshow",
    "n_policy_decline",
    "n_guarantee",
    "n_check_in",
    "n_room_wait",
    "n_room_ready",
    "n_in_house",
    "n_folio",
    "n_charge",
    "n_check_out",
    "n_late_checkout",
    "n_early_checkout",
    "n_key_reissue",
    "n_adjustment",
    "n_refund_request",
    "n_refund_post",
    "n_dispute_open",
    "n_dispute_close",
    "n_contact",
    "n_settle",
    "n_duplicate_events",
)

EVENT_LABELS: dict[str, str] = {
    "search": "Search",
    "quote": "Quote",
    "hold": "Hold",
    "hold_expire": "Hold expired",
    "payment_fail": "Payment failed",
    "payment_retry": "Payment retry",
    "payment_capture": "Payment captured",
    "modify": "Modification",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "noshow": "Did not arrive",
    "policy_decline": "Policy decline",
    "guarantee": "Guarantee",
    "check_in": "Check-in",
    "room_wait": "Room not ready",
    "room_ready": "Room ready",
    "in_house": "Still in house",
    "folio": "Folio post",
    "charge": "Charge",
    "check_out": "Check-out",
    "late_checkout": "Late checkout",
    "early_checkout": "Early checkout",
    "key_reissue": "Key reissue",
    "adjustment": "Adjustment",
    "refund_request": "Refund requested",
    "refund_post": "Refund posted",
    "dispute_open": "Dispute opened",
    "dispute_close": "Dispute closed",
    "contact": "Support contact",
    "settle": "Folio settled",
}

-- Roll linked events up to one feature row per reservation.

CREATE OR REPLACE TABLE case_input AS
SELECT
    reservation_id,
    any_value(guest_id) AS guest_id,
    any_value(property_id) AS property_id,
    any_value(booking_value_cents) AS booking_value_cents,
    any_value(nights) AS nights,
    any_value(arrival_day) AS arrival_day,
    count(*) FILTER (WHERE event_type = 'search') AS n_search,
    count(*) FILTER (WHERE event_type = 'quote') AS n_quote,
    count(*) FILTER (WHERE event_type = 'hold') AS n_hold,
    count(*) FILTER (WHERE event_type = 'hold_expire') AS n_hold_expire,
    count(*) FILTER (WHERE event_type = 'confirm') AS n_confirm,
    count(*) FILTER (WHERE event_type = 'modify') AS n_modify,
    count(*) FILTER (WHERE event_type = 'cancel') AS n_cancel,
    count(*) FILTER (WHERE event_type = 'policy_decline') AS n_policy_decline,
    count(*) FILTER (WHERE event_type = 'noshow') AS n_noshow,
    count(*) FILTER (WHERE event_type = 'payment_fail') AS n_payment_fail,
    count(*) FILTER (WHERE event_type = 'payment_retry') AS n_payment_retry,
    count(*) FILTER (WHERE event_type = 'payment_capture') AS n_payment_capture,
    count(*) FILTER (WHERE event_type = 'guarantee') AS n_guarantee,
    count(*) FILTER (WHERE event_type = 'check_in') AS n_check_in,
    count(*) FILTER (WHERE event_type = 'room_ready') AS n_room_ready,
    count(*) FILTER (WHERE event_type = 'room_wait') AS n_room_wait,
    count(*) FILTER (WHERE event_type = 'folio') AS n_folio,
    count(*) FILTER (WHERE event_type = 'check_out') AS n_check_out,
    count(*) FILTER (WHERE event_type = 'charge') AS n_charge,
    count(*) FILTER (WHERE event_type = 'adjustment') AS n_adjustment,
    count(*) FILTER (WHERE event_type = 'refund_request') AS n_refund_request,
    count(*) FILTER (WHERE event_type = 'refund_post') AS n_refund_post,
    count(*) FILTER (WHERE event_type = 'dispute_open') AS n_dispute_open,
    count(*) FILTER (WHERE event_type = 'dispute_close') AS n_dispute_close,
    count(*) FILTER (WHERE event_type = 'contact') AS n_contact,
    count(*) FILTER (WHERE event_type = 'settle') AS n_settle,
    0 AS n_duplicate_charge,
    count(*) FILTER (WHERE event_type = 'late_checkout') AS n_late_checkout,
    count(*) FILTER (WHERE event_type = 'early_checkout') AS n_early_checkout,
    count(*) FILTER (WHERE event_type = 'key_reissue') AS n_key_reissue,
    count(*) FILTER (WHERE event_type = 'in_house') AS n_in_house,
    0 AS n_duplicate_events,
    count(*) AS n_raw_events
FROM linked_events
GROUP BY reservation_id;

UPDATE case_input
SET n_duplicate_charge = 1
WHERE reservation_id IN (
    SELECT reservation_id
    FROM linked_events
    WHERE event_type = 'charge'
    GROUP BY reservation_id, amount_cents
    HAVING count(*) >= 2
);

-- Stage raw events: drop exact duplicates, keep sequence order when time is late.

CREATE OR REPLACE TABLE staged_events AS
SELECT
    event_id,
    reservation_id,
    guest_id,
    property_id,
    event_type,
    event_seq,
    event_time,
    amount_cents,
    booking_value_cents,
    nights,
    arrival_day,
    row_number() OVER (
        PARTITION BY reservation_id, event_type, event_seq, amount_cents
        ORDER BY event_id
    ) AS dup_rank
FROM raw_events
WHERE reservation_id IS NOT NULL
  AND event_type IS NOT NULL;

CREATE OR REPLACE TABLE linked_events AS
SELECT
    event_id,
    reservation_id,
    guest_id,
    property_id,
    event_type,
    event_seq,
    event_time,
    amount_cents,
    booking_value_cents,
    nights,
    arrival_day,
    row_number() OVER (
        PARTITION BY reservation_id
        ORDER BY event_seq, event_time, event_id
    ) AS process_order
FROM staged_events
WHERE dup_rank = 1;

-- Name the journey variant from event counts. A missing event is not a failure.

CREATE OR REPLACE TABLE classified AS
WITH labeled AS (
    SELECT
        *,
        CASE
            WHEN n_policy_decline > 0 THEN 'policy_block'
            WHEN n_noshow > 0 THEN 'voluntary_noshow'
            WHEN n_cancel > 0
                 AND n_payment_fail < 2
                 AND n_dispute_open = 0
                 AND n_hold_expire = 0
                 AND n_modify < 3
                 AND n_room_wait = 0
                 AND n_adjustment = 0
                 AND n_duplicate_charge = 0
                 AND n_refund_request = 0 THEN 'voluntary_cancel'
            WHEN n_in_house > 0 THEN 'censored'
            WHEN n_check_in = 0
                 AND n_check_out > 0
                 AND n_payment_fail < 2
                 AND n_modify < 3
                 AND n_dispute_open = 0
                 AND n_room_wait = 0 THEN 'telemetry_gap'
            WHEN n_payment_fail >= 2 THEN 'payment_retry'
            WHEN n_hold_expire > 0 THEN 'hold_expired'
            WHEN n_payment_capture > 0 AND n_payment_fail > 0 THEN 'tender_mismatch'
            WHEN n_modify >= 3 THEN 'modification_loop'
            WHEN n_duplicate_charge > 0 THEN 'duplicate_charge'
            WHEN n_dispute_open > 0 THEN 'folio_dispute'
            WHEN n_refund_request > 0 AND n_contact > 0 THEN 'refund_stall'
            WHEN n_adjustment > 0 AND n_contact > 0 THEN 'rate_reprice'
            WHEN n_room_wait > 0 THEN 'room_not_ready'
            WHEN n_late_checkout > 0 THEN 'late_checkout'
            WHEN n_early_checkout > 0 THEN 'early_checkout'
            WHEN n_key_reissue > 0 THEN 'key_reissue'
            WHEN n_contact > 0 THEN 'amenity_contact'
            WHEN n_adjustment > 0 THEN 'rate_absorbed'
            ELSE 'clean'
        END AS variant
    FROM case_input
)
SELECT
    *,
    CASE
        WHEN variant IN (
            'policy_block', 'voluntary_cancel', 'voluntary_noshow',
            'telemetry_gap', 'censored', 'clean'
        ) THEN 0
        WHEN variant = 'payment_retry' THEN CASE WHEN n_confirm = 0 THEN 1 ELSE 0 END
        WHEN variant = 'hold_expired' THEN CASE WHEN n_confirm = 0 THEN 1 ELSE 0 END
        WHEN variant = 'room_not_ready' THEN CASE WHEN n_check_out = 0 THEN 1 ELSE 0 END
        WHEN variant = 'modification_loop' THEN CASE WHEN n_check_out = 0 THEN 1 ELSE 0 END
        WHEN variant = 'tender_mismatch' THEN CASE WHEN n_check_out = 0 THEN 1 ELSE 0 END
        WHEN variant = 'rate_reprice' THEN CASE WHEN n_cancel > 0 OR n_check_out = 0 THEN 1 ELSE 0 END
        WHEN variant = 'folio_dispute' THEN CASE WHEN n_dispute_close = 0 THEN 1 ELSE 0 END
        WHEN variant = 'duplicate_charge' THEN CASE WHEN n_adjustment = 0 THEN 1 ELSE 0 END
        WHEN variant = 'refund_stall' THEN CASE WHEN n_refund_post = 0 THEN 1 ELSE 0 END
        WHEN variant IN (
            'late_checkout', 'early_checkout', 'key_reissue',
            'amenity_contact', 'rate_absorbed'
        ) THEN CASE WHEN n_check_out = 0 THEN 1 ELSE 0 END
        ELSE 0
    END AS dropoff
FROM labeled;

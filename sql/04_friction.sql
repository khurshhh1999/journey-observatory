-- Rank operational variants and cut the high-friction group at the score gap.

CREATE OR REPLACE TABLE variant_stats AS
WITH operational AS (
    SELECT *
    FROM classified
    WHERE variant NOT IN (
        'policy_block', 'voluntary_cancel', 'voluntary_noshow',
        'telemetry_gap', 'censored', 'clean'
    )
),
stats AS (
    SELECT
        variant,
        count(*) AS cases,
        sum(dropoff) AS dropoff_cases,
        sum(dropoff) * 1.0 / count(*) AS dropoff_rate,
        sum(dropoff) * 1.0 AS score,
        sum(n_contact) AS contacts,
        sum(CASE WHEN dropoff = 1 THEN booking_value_cents ELSE 0 END) AS dropoff_value_cents
    FROM operational
    GROUP BY variant
),
ordered AS (
    SELECT
        *,
        lead(score) OVER (ORDER BY score DESC, variant) AS next_score
    FROM stats
),
cut AS (
    SELECT score AS cut_score
    FROM ordered
    WHERE next_score IS NOT NULL
      AND next_score < score * {{gap_ratio}}
    ORDER BY score DESC
    LIMIT 1
)
SELECT
    ordered.*,
    CASE
        WHEN ordered.score >= (SELECT cut_score FROM cut) THEN 1
        ELSE 0
    END AS high_friction,
    row_number() OVER (ORDER BY ordered.score DESC, ordered.variant) AS rank
FROM ordered;

WITH movie_weeks AS (
    SELECT
        movie_title,
        week_start,
        week_number,
        theaters,
        days_in_release,
        per_theater,
        LAG(per_theater) OVER (
            PARTITION BY movie_title
            ORDER BY week_number
        ) AS prev_per_theater
    FROM box_office
),
changes AS (
    SELECT
        movie_title,
        week_start,
        week_number,
        theaters,
        days_in_release,
        per_theater,
        prev_per_theater,
        CASE
            WHEN prev_per_theater IS NOT NULL AND prev_per_theater != 0
            THEN (per_theater - prev_per_theater) / prev_per_theater
            ELSE NULL
        END AS pct_change_per_theater
    FROM movie_weeks
)
SELECT
    movie_title,
    week_start,
    theaters,
    days_in_release,
    per_theater,
    pct_change_per_theater,
    CASE
        WHEN pct_change_per_theater <= -0.45 AND theaters >= 1000 AND days_in_release > 7
            THEN 'REDUCE'
        WHEN pct_change_per_theater > -0.15 AND theaters >= 500
            THEN 'HOLD_OR_SUPPORT'
        WHEN pct_change_per_theater > 0
            THEN 'EXPAND_OR_SUPPORT'
        ELSE 'HOLD'
    END AS recommendation
FROM changes
WHERE prev_per_theater IS NOT NULL
ORDER BY week_start, recommendation, per_theater DESC;
WITH movie_weeks AS (
    SELECT
        movie_title,
        week_start,
        week_number,
        per_theater,
        weekly_gross,
        theaters,
        days_in_release,
        LAG(per_theater) OVER (
            PARTITION BY movie_title
            ORDER BY week_number
        ) AS prev_per_theater
    FROM box_office
)
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
ORDER BY movie_title, week_number;
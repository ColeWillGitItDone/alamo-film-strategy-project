SELECT COUNT(*) AS total_rows
FROM box_office;

SELECT COUNT(DISTINCT movie_title) AS unique_titles
FROM box_office;

SELECT week_start,
       AVG(per_theater) AS avg_per_theater,
       AVG(weekly_gross) AS avg_weekly_gross,
       COUNT(*) AS titles_in_chart
FROM box_office
GROUP BY week_start
ORDER BY week_start;

SELECT is_new_release,
       AVG(per_theater) AS avg_per_theater,
       AVG(weekly_gross) AS avg_weekly_gross,
       COUNT(*) AS title_count
FROM box_office
GROUP BY is_new_release;
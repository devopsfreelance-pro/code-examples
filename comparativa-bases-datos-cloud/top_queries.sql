-- Identifica las queries mas costosas, el mismo enfoque que documenta el
-- post para PostgreSQL en RDS o Cloud SQL (pg_stat_statements).
SELECT
    query,
    calls,
    round(total_exec_time::numeric, 2) AS total_time_ms,
    round(mean_exec_time::numeric, 2) AS mean_time_ms,
    round(max_exec_time::numeric, 2) AS max_time_ms
FROM pg_stat_statements
WHERE query NOT ILIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC
LIMIT 10;

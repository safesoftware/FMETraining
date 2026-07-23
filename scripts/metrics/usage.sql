-- KNOW-2166 — training-updates app usage / adoption metrics.
--
-- Run these against the prod Postgres DB (e.g. via the AWS console query
-- editor). They answer "is the team actually leaning on the tool in the
-- release cycle?" WITHOUT depending on the in-app accept/reject workflow
-- (reviewers often just read the report, then edit directly in Skilljar).
--
-- Query A works today (reads the `runs` table).
-- Queries B and C need migration 0005 (`report_views`) deployed and some
-- report opens recorded — they return no rows until then.
--
-- These are also exposed programmatically at GET /api/metrics/usage and in
-- the "Usage" panel (KNOW-2166); this file is the raw-SQL fallback.


-- A. Runs generated per release cycle, attributed to a user. (available now)
--    "Who kicked off the tool, for which FME version, how often."
SELECT COALESCE(u.email, '(unknown)') AS "user",
       r.to_version,
       count(*)                       AS runs
FROM runs r
LEFT JOIN users u ON u.id = r.created_by
GROUP BY u.email, r.to_version
ORDER BY r.to_version DESC, runs DESC;


-- B. Report opens per release cycle, by whom. (needs 0005 deployed)
--    Captures the "referring to the edits" behaviour: every authenticated
--    open of a run's HTML report, even when the reviewer never accepts a
--    single suggestion in-app.
SELECT COALESCE(u.email, '(deleted)')  AS "user",
       r.to_version,
       count(*)                        AS opens,
       count(DISTINCT v.run_id)        AS reports_opened,
       max(v.viewed_at)                AS last_open
FROM report_views v
JOIN runs r        ON r.id = v.run_id
LEFT JOIN users u  ON u.id = v.user_id
GROUP BY u.email, r.to_version
ORDER BY r.to_version DESC, opens DESC;


-- C. Adoption headline: distinct viewers per release cycle. (needs 0005)
--    This is the primary "dependable enough for the whole team to use"
--    signal — how many distinct people opened a report for each version.
SELECT r.to_version,
       count(DISTINCT v.user_id) AS distinct_viewers,
       count(*)                  AS opens
FROM report_views v
JOIN runs r ON r.id = v.run_id
GROUP BY r.to_version
ORDER BY r.to_version DESC;

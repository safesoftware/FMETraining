# FME Academy Backup Navigator

Builds a single page that groups every FME Academy lesson backup in `s3://safeskilljar/` by
learning path → course → lesson (in Academy order), with every older version of each lesson.

## Pipeline

| Step | Script | Input | Output |
|---|---|---|---|
| 1 | `list_s3.py` | public bucket listing (anonymous) | `data/s3_lessons.json` |
| 2 | `fetch_skilljar.py` | Skilljar API (`SKILLJAR_API_KEY`) | `data/skilljar_snapshot.json` |
| 3 | `build_map.py` | 1 + 2 + previous `academy-map.json` + `config.json` | `academy-map.json` (committed), `run.json` |
| 4 | `build_page.py` | `academy-map.json` + `template.html` | `dist/index.html` (self-contained) |

`build_navigator.yml` runs these after each S3 sync and uploads to `s3://safeskilljar/navigator/`.

## Rules

- **Version** = first folder of the S3 key (the scraper's version tag).
- **Punctuation duplicates** from older scraper runs (`?` / `.` / `_`) are collapsed; newest copy wins.
- **Matching is by course title across all path folders**: the scraper stores a course once even when
  it sits in several paths, so one copy can appear under every path containing that course.
  - Versioned paths (`…-2023-1`) match the exact course title, including version.
  - Current paths match the title without its version; the highest version is shown as current,
    the rest as "older".
- **Nothing disappears**: paths, courses and lessons that drop out of Skilljar stay in
  `academy-map.json`, marked `removed`.
- **Public repo safety**: hidden paths and other domains are excluded from the map; the API script
  only calls structural endpoints and never prints responses.

## config.json

- `path_folder_aliases`: S3 folder → Skilljar path slug, when they differ.
- `lesson_titles_not_backed_up`: lesson titles that are never scraped (not flagged as missing).
- `exclude_course_title_patterns`: test/clone courses kept out of the standalone list.

## Still to confirm before going live

- A **read-only Skilljar v1 API key** (Skilljar dashboard: Organization settings, then API
  Credentials). `fetch_skilljar.py` uses the documented v1 API (https://api.skilljar.com/docs/) with
  HTTP Basic auth: key as username, blank password. The starting `academy-map.json` was built through
  the Skilljar connector (v2); if v1 IDs differ, entries still match by path slug and course/lesson title.
- IAM role for GitHub OIDC limited to `s3:PutObject` on `safeskilljar/navigator/*`, with its ARN in
  the `AWS_NAVIGATOR_ROLE_ARN` secret and the key in `SKILLJAR_API_KEY`, both in a GitHub
  Environment named `navigator` restricted to `main`.

## Notes

- `sync_s3.yml` excludes `navigator/*` so the published page is never synced back into this repo.
- The workflow writes its working files to `$RUNNER_TEMP`; only `academy-map.json` is committed.
  (Don't add dotfiles here: the sync job deletes every dotfile in the repo before it runs.)
- To run locally: `python3 list_s3.py data/s3_lessons.json`, then `build_map.py` and `build_page.py`
  as in the workflow, and open `dist/index.html`.

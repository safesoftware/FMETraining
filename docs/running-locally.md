# Running Locally — the FastAPI web app (and the legacy serve.py launcher)

The **FastAPI multi-user web app under `app/` is the app to use** — it is the
full launcher, run history, report viewer, and Lesson Edits surface, and it is
what runs in production. The legacy `serve.py` launcher is superseded and kept
only for one not-yet-ported feature.

| App | Port | Start | Use it for |
|-----|-----:|-------|------------|
| **`app/` (FastAPI)** — primary | **8000** | `make up` (Docker Compose; also brings up postgres + minio + worker). Non-Docker: `uvicorn app.main:app --reload`. | Everything: launching runs, run history, viewing/regenerating reports, Lesson Edits + drafts. **QA all new web-app work here.** |
| `serve.py` (legacy) | 8080 | `python serve.py` (also invoked by `launch.sh` / `launch.bat`) | **Only** the Skilljar release flow (push / archive / releases, draft-course linking) that hasn't been ported to the FastAPI app yet — see KNOW-2307 / KNOW-2323. |

## Health checks

- FastAPI app: `curl http://localhost:8000/health` → `{"status":"ok",...}`; or open `http://localhost:8000/` and sign in.
- Legacy launcher: open `http://localhost:8080/` (it now shows a deprecation banner pointing back here).

## Why two apps (still)?

The legacy `serve.py` is a thin `BaseHTTPServer` wrapping the pipeline CLI for a
single local user — the original UI. The app was rewritten as the FastAPI
service under `app/` (multi-user auth, Postgres-backed job queue, run
scheduling, background worker); see
`docs/plans/2026-04-29-multi-user-web-app.md`. The FastAPI app is now the
**deployed production app** (single EC2 —
`docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md`).

The only thing the FastAPI app does **not** yet have is the Skilljar publish /
archive / release flow, which still lives in `serve.py` + `pipeline/`. Once that
ports across (KNOW-2307 / KNOW-2323), `serve.py`, `launcher.html`, and
`launch.sh` / `launch.bat` can be retired — tracked by the "retire the legacy
launcher" ticket.

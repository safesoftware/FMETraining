# Running Locally — serve.py and the new FastAPI app

The repo currently has **two** web apps that coexist during the multi-user web
app rebuild:

| App                   | Default port | Start command                       | Purpose                                                                                       |
|-----------------------|-------------:|-------------------------------------|-----------------------------------------------------------------------------------------------|
| `serve.py` (legacy)   | **8080**     | `python serve.py`                   | The existing browser launcher + report viewer. Keep running on 8080 — `launch.sh`/`.bat` use it. |
| `app/` (new, FastAPI) | **8000**     | `uvicorn app.main:app --reload`     | Phase 0 skeleton for the multi-user web app (KNOW-2257 onward).                               |

Run them in **separate terminals**. They are independent processes — neither
imports from the other and they share no in-memory state. Port collisions are
the only failure mode, so do not start uvicorn on 8080 unless you have first
stopped `serve.py`.

## Health checks

- `serve.py`: open `http://localhost:8080/` in a browser.
- FastAPI:   `curl http://localhost:8000/health` returns `{"status":"ok",...}`.

## Why two apps?

The legacy `serve.py` is a thin Python `BaseHTTPServer` that wraps the
existing pipeline CLI for a single local user. The new `app/` is a FastAPI
service that will (in later tickets) add multi-user auth, a Postgres-backed
job queue, and run scheduling — see
`docs/plans/2026-04-29-multi-user-web-app.md` for the application design.
They ship side-by-side until the FastAPI app reaches feature parity, then
`serve.py` retires. Production deployment of the FastAPI app follows
`docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md` (single EC2).

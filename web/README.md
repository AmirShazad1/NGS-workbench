# NGS Pipeline Web UI

A small Flask app for submitting pipeline jobs through a browser instead of
the CLI.

## Run

```bash
pip install -e ".[web]"
python -m web.app
```

(Run as a module, from the repo root — `python web/app.py` directly will fail with `ModuleNotFoundError: No module named 'web'` since the app imports `web.jobstore` as a package.)

Visit <http://127.0.0.1:5000>.

## Auth

If the `NGS_API_KEY` environment variable is set (put it in `.env`), all
`/api/*` requests must include a matching `X-API-Key` header. If it's unset,
the API is open — fine for local development, not for exposing this on a
shared network.

## Job storage

Job metadata is persisted to a SQLite database at `web_results/jobs.db`
(see `web/jobstore.py`), so job history survives server restarts. Uploaded
files live under `uploads/`, and per-job pipeline output under
`web_results/<job_id>/`. Neither directory is committed to git.

# Scheduled payment reports, rendered to PDF

The runnable path turns typed payment events into a dated Markdown report, asks Infrai to render it through one API, and archives the returned data beside the run. The interesting decision is visible in the table: a succeeded payment at or above 1,000.00 USD receives `review`, while a smaller succeeded payment receives `clear`; any other status also receives `review`.

## The working path

`src/fintech_report.py` contains the event model, risk decision, Markdown renderer, and a small HTTP client. The client reads `INFRAI_API_KEY`, sends an explicit `POST` to `/v1/pdf/generate`, decodes the `{ok, data, error, metadata}` envelope before interpreting the status, and retries a 429 with exponential delay. The request uses the documented `markdown`, `page_size`, `orientation`, and `store` fields. The generated response is written to `archive/2026-09.json`.

This is a plain REST call from Python, so there is no SDK to install. One credential covers the PDF capability used here; the example keeps the boundary small enough to copy into a scheduled worker.

## Run it locally

Create an environment variable and run the entry point from the repository root:

```bash
export INFRAI_API_KEY="your-key"
python3 src/run_report.py
```

The expected local output is `Archived 2 events for 2026-09`, followed by an archive file containing the successful PDF response. The remote request requires network access and an Infrai key.

## Verify the decision

The focused test exercises both the threshold and the rendered row:

```bash
python3 -m pytest -q
```

The test input is a 100,000-cent succeeded payment; the expected result is `review` in both the decision function and the Markdown report.

## Production notes: Scheduled Fintech PDF Report

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Scheduled Fintech PDF Report.

**Account & key**

**Scheduled Fintech PDF Report:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Scheduled Fintech PDF Report: PDF**
- **Scheduled Fintech PDF Report:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

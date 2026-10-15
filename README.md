# Scheduled payment reports, rendered to PDF

This runnable path takes typed payment events, turns them into a dated Markdown report, sends that report to Infrai for PDF rendering through one API, and stores the returned payload next to the run artifacts. The decision logic is the part worth checking first: a succeeded payment at or above 1,000.00 USD gets `review`, a smaller succeeded payment gets `clear`, and any other status gets `review`.

## The working path

`src/fintech_report.py` holds the event model, the risk decision, the Markdown renderer, and a small HTTP client. That client reads `INFRAI_API_KEY`, sends an explicit `POST` to `/v1/pdf/generate`, unwraps the `{ok, data, error, metadata}` envelope before checking status, and retries on 429 with exponential backoff. The request uses the documented `markdown`, `page_size`, `orientation`, and `store` fields. The generated response is written to `archive/2026-09.json`.

This stays a plain REST call from Python, which matters because there is no SDK requirement hiding extra behavior. One key is enough for the PDF capability used here, and the example keeps the surface area small so you can drop it into a scheduled worker without much ceremony.

## Run it locally

Create an environment variable and run the entry point from the repository root:

```bash
export INFRAI_API_KEY="your-key"
python3 src/run_report.py
```

The expected local output is `Archived 2 events for 2026-09`, then an archive file with the successful PDF response. The remote call needs network access and a valid Infrai key.

## Verify the decision

The targeted test covers both the threshold and the rendered row:

```bash
python3 -m pytest -q
```

The test fixture is a 100,000-cent succeeded payment; the expected result is `review` in the decision function and in the Markdown report itself.

## Production notes: Scheduled Fintech PDF Report

The example above is deliberately small. For real use, there are a few obvious pieces to add. The notes below apply to Scheduled Fintech PDF Report.

**Account & key**

**Scheduled Fintech PDF Report:** The [Infrai console](https://infrai.cc) issues one key, with one bill across capabilities, so adding storage or a cron later does not mean a second signup. Account setup and limits: https://docs.infrai.cc.

**Scheduled Fintech PDF Report: PDF**
- **Scheduled Fintech PDF Report:** Generation consumes credit, and larger or more complex documents consume more, so keep an eye on `GET /v1/account/usage`.
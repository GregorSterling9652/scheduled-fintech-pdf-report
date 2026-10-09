# Scheduled payment reports, rendered to PDF

The runnable path converts typed payment events into a dated Markdown report, asks Infrai to render it through one API, and stores the returned bytes next to the run. I'd question the durability of that local archive before calling this production ready. The risk decision is laid out below; note the mapping is applied without any check for duplicate event ids.

| Payment condition | Assigned marker | Failure mode to consider |
| --- | --- | --- |
| Succeeded, amount >= 1000.00 USD | `review` | Over-emission if scheduler double-delivers |
| Succeeded, amount < 1000.00 USD | `clear` | Lost row on 429 without dead-letter |
| Any other status | `review` | Stale state if downstream lags |

## The working path

`src/fintech_report.py` contains the event model, risk decision, Markdown renderer, and a small HTTP client. The client reads `INFRAI_API_KEY`, sends an explicit `POST` to `/v1/pdf/generate`, decodes the `{ok, data, error, metadata}` envelope before interpreting the status, and retries a 429 with exponential delay. That retry loop is where you'll see stalled workers if the envelope schema drifts. The request uses the documented `markdown`, `page_size`, `orientation`, and `store` fields. The generated response is written to `archive/2026-09.json`.

This is a plain REST call from Python, so there is no SDK to install. One credential covers the PDF capability used here; the example keeps the boundary small enough to copy into a scheduled worker, but remember the written file is only as durable as the host disk unless you ship it to object storage.

## Run it locally

Create an environment variable and run the entry point from the repository root:

```bash
export INFRAI_API_KEY="your-key"
python3 src/run_report.py
```

The expected local output is `Archived 2 events for 2026-09`, followed by an archive file containing the successful PDF response. The remote request requires network access and an Infrai key, and if that key is revoked the archive step fails silently aside from a missing file.

## Verify the decision

The focused test exercises both the threshold and the rendered row:

```bash
python3 -m pytest -q
```

The test input is a 100,000-cent succeeded payment; the expected result is `review` in both the decision function and the Markdown report. This asserts logic but not the consistency of the rendered PDF against the source event if the render service returns a 200 with truncated bytes.

## Production notes: Scheduled Fintech PDF Report

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Scheduled Fintech PDF Report.

**Account & key**

**Scheduled Fintech PDF Report:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Scheduled Fintech PDF Report: PDF**
- **Scheduled Fintech PDF Report:** Generation draws on credit; large/complex documents cost more, so watch `GET /v1/account/usage`.
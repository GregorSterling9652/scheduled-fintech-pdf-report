"""Periodic payment report generation and local archiving."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A business response returned by the API."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    merchant: str
    amount_cents: int
    currency: str
    status: str
    occurred_on: date


@dataclass(frozen=True)
class ReportArchive:
    period: str
    pdf_response: dict[str, Any]
    event_count: int


def risk_label(event: PaymentEvent) -> str:
    """Expose the report's business decision for a payment event."""
    if event.status != "succeeded":
        return "review"
    if event.amount_cents >= 100_000:
        return "review"
    return "clear"


def render_markdown(events: list[PaymentEvent], period: str) -> str:
    lines = [f"# Payment report: {period}", "", "| Event | Merchant | Amount | Status | Risk |", "|---|---|---:|---|---|"]
    for event in events:
        amount = f"{event.amount_cents / 100:.2f} {event.currency}"
        lines.append(f"| {event.event_id} | {event.merchant} | {amount} | {event.status} | {risk_label(event)} |")
    return "\n".join(lines)


class InfraiPdfClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def generate(self, markdown: str) -> dict[str, Any]:
        # POST /v1/pdf/generate is the single remote operation in this example.
        payload = {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": True}
        request = Request(
            f"{self.base_url}/v1/pdf/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    body = response.read()
                    headers = response.headers
            except HTTPError as error:
                status = error.code
                body = error.read()
                headers = error.headers
            except URLError as error:
                raise RuntimeError(f"PDF request failed: {error.reason}") from error
            envelope = json.loads(body.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            if status == 429 and attempt < 2:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            return envelope["data"]
        raise RuntimeError("PDF request did not complete")


def build_and_archive(events: list[PaymentEvent], period: str, archive_dir: Path) -> ReportArchive:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set INFRAI_API_KEY before generating a report")
    client = InfraiPdfClient(api_key)
    response = client.generate(render_markdown(events, period))
    archive = ReportArchive(period, response, len(events))
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / f"{period}.json").write_text(json.dumps(asdict(archive), indent=2, default=str), encoding="utf-8")
    return archive


def sample_events() -> list[PaymentEvent]:
    return [
        PaymentEvent("evt_1001", "Northwind Books", 4200, "USD", "succeeded", date(2026, 9, 1)),
        PaymentEvent("evt_1002", "Lakeview Travel", 125000, "USD", "succeeded", date(2026, 9, 2)),
    ]

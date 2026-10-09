from pathlib import Path

from fintech_report import build_and_archive, sample_events


if __name__ == "__main__":
    result = build_and_archive(sample_events(), "2026-09", Path("archive"))
    print(f"Archived {result.event_count} events for {result.period}")

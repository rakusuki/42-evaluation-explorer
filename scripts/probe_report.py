from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.services.capability import capability_report_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a sanitized 42 API capability report."
    )
    parser.add_argument(
        "--login",
        required=True,
        help="42 login to probe",
    )
    parser.add_argument(
        "--project",
        help=(
            "Optional 42 project ID or slug. Including it tests "
            "project/scales access."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/capability-report.json"),
        help=(
            "Output JSON path "
            "(default: reports/capability-report.json)"
        ),
    )
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()
    report = await capability_report_service.build(
        args.login,
        args.project,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Capability report written to {args.output}")
    print(
        json.dumps(
            report["findings"],
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())

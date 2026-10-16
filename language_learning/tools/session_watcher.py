#!/usr/bin/env python3
"""Watch an mGBA learner snapshot and refresh profile/review outputs."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import profile_sync


Signature = tuple[int, int]


def signature(path: Path) -> Signature:
    stat = path.stat()
    return stat.st_mtime_ns, stat.st_size


def sync_changed(profile: Path, snapshot: Path, previous: Signature | None, *,
                 review_output: Path | None = None,
                 dashboard_output: Path | None = None,
                 variant_output: Path | None = None,
                 runtime_output: Path | None = None,
                 review_limit: int = 20,
                 include_upcoming: bool = False,
                 allow_reset: bool = False) -> tuple[Signature, bool]:
    current = signature(snapshot)
    if current == previous:
        return current, False
    profile_sync.synchronize(
        profile, snapshot, allow_reset=allow_reset,
        review_output=review_output, dashboard_output=dashboard_output,
        variant_output=variant_output,
        runtime_output=runtime_output,
        review_limit=review_limit, include_upcoming=include_upcoming,
    )
    return current, True


def _say(message: str) -> None:
    sys.stdout.buffer.write((message + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--review-output", type=Path)
    parser.add_argument("--dashboard-output", type=Path)
    parser.add_argument("--variant-output", type=Path)
    parser.add_argument("--runtime-output", type=Path)
    parser.add_argument("--review-limit", type=int, default=20)
    parser.add_argument("--include-upcoming", action="store_true")
    parser.add_argument("--allow-reset", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument("--once", action="store_true", help="synchronize once and exit")
    args = parser.parse_args()
    if args.poll_seconds <= 0:
        parser.error("--poll-seconds must be greater than zero")
    previous = None
    while True:
        try:
            previous, changed = sync_changed(
                args.profile, args.snapshot, previous,
                review_output=args.review_output,
                dashboard_output=args.dashboard_output,
                variant_output=args.variant_output,
                runtime_output=args.runtime_output,
                review_limit=args.review_limit,
                include_upcoming=args.include_upcoming,
                allow_reset=args.allow_reset,
            )
            if changed:
                _say(f"Synchronized learner snapshot: {args.snapshot}")
            if args.once:
                return 0
        except (OSError, ValueError) as error:
            if args.once:
                raise
            _say(f"Waiting for a complete learner snapshot: {error}")
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())

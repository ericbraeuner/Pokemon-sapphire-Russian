#!/usr/bin/env python3
"""Create a one-folder mGBA adaptive learner runtime for a profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _lua_string(path: Path | str) -> str:
    value = str(path).replace("\\", "/")
    return json.dumps(value, ensure_ascii=False)


def _replace_setting(source: str, name: str, value: str) -> str:
    updated, count = re.subn(
        rf'^local {re.escape(name)} = .+$',
        f"local {name} = {value}", source, count=1, flags=re.MULTILINE,
    )
    if count != 1:
        raise ValueError(f"mGBA template setting not found: {name}")
    return updated


def _write(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _cmd_quote(value: Path | str) -> str:
    return f'"{str(value).replace("%", "%%")}"'


def configure(profile_path: Path, output_dir: Path, *,
              python_executable: Path | str = sys.executable) -> dict[str, Path]:
    profile_path = profile_path.resolve()
    output_dir = output_dir.resolve()
    profile: dict[str, Any] = json.loads(profile_path.read_text(encoding="utf-8"))
    profile_id = profile["profile_id"]
    if not isinstance(profile_id, str) or not profile_id:
        raise ValueError("profile_id is required")
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot = output_dir / "learner-snapshot.json"
    runtime_plan = output_dir / "adaptive-runtime.lua"
    exporter_path = output_dir / "export_learner_snapshot.lua"
    adaptive_path = output_dir / "apply_adaptive_plan.lua"
    launcher_path = output_dir / "learner_runtime.lua"
    start_path = output_dir / "start_learner_sync.cmd"

    exporter = (ROOT / "mgba/export_learner_snapshot.lua").read_text(encoding="utf-8")
    exporter = _replace_setting(exporter, "OUTPUT_PATH", _lua_string(snapshot))
    exporter = _replace_setting(exporter, "SOURCE_ID", _lua_string(profile_id))
    _write(exporter_path, exporter)

    adaptive = (ROOT / "mgba/apply_adaptive_plan.lua").read_text(encoding="utf-8")
    adaptive = _replace_setting(adaptive, "PLAN_PATH", _lua_string(runtime_plan))
    _write(adaptive_path, adaptive)

    launcher = (
        "-- Generated learner runtime: load only this file in mGBA Tools > Scripting.\n"
        f"dofile({_lua_string(exporter_path)})\n"
        f"dofile({_lua_string(adaptive_path)})\n"
    )
    _write(launcher_path, launcher)

    watcher = ROOT / "tools/session_watcher.py"
    review = output_dir / "review-queue.json"
    dashboard = output_dir / "learner-progress.html"
    plan = output_dir / "adaptive-plan.json"
    command = " ".join([
        _cmd_quote(python_executable), _cmd_quote(watcher), _cmd_quote(profile_path), _cmd_quote(snapshot),
        "--review-output", _cmd_quote(review), "--dashboard-output", _cmd_quote(dashboard),
        "--variant-output", _cmd_quote(plan), "--runtime-output", _cmd_quote(runtime_plan),
    ])
    _write(start_path, "@echo off\n" + command + "\npause\n")
    return {
        "launcher": launcher_path, "watcher": start_path, "snapshot": snapshot,
        "runtime_plan": runtime_plan, "dashboard": dashboard,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("build/learner_runtime"))
    args = parser.parse_args()
    files = configure(args.profile, args.output_dir)
    print(f"Runtime folder: {args.output_dir.resolve()}")
    print(f"1. Start: {files['watcher']}")
    print(f"2. Load in mGBA Tools > Scripting: {files['launcher']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prove that frozen PLUMED text series align with a GROMACS checkpoint."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import re
import sys


class ValidationError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plumed", required=True, type=Path)
    parser.add_argument("--base-dir", required=True, type=Path)
    parser.add_argument("--checkpoint-time", required=True, type=float)
    parser.add_argument("--dt", required=True, type=float)
    return parser.parse_args()


def file_token(line: str) -> str | None:
    match = re.search(r"(?:^|\s)FILE=([^\s,;]+)", line)
    return match.group(1) if match else None


def positive_integer_token(text: str, key: str) -> int:
    match = re.search(rf"(?:^|\s){re.escape(key)}=([0-9]+)(?:\s|$)", text)
    if not match or int(match.group(1)) < 1:
        raise ValidationError(f"cannot find positive {key}= in PLUMED input")
    return int(match.group(1))


def declared_series(path: Path) -> dict[str, tuple[int, bool]]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        lines.append(raw.split("#", 1)[0].strip())
    pace = positive_integer_token(" ".join(lines), "PACE") if any("FILE=HILLS" in line for line in lines) else None
    result: dict[str, tuple[int, bool]] = {}
    for line in lines:
        target = file_token(line)
        if target is None:
            continue
        target_path = Path(target)
        if target_path.is_absolute() or ".." in target_path.parts or len(target_path.parts) != 1:
            raise ValidationError(f"unsafe/nonlocal FILE target: {target}")
        if target == "HILLS":
            assert pace is not None
            result[target] = (pace, False)
        elif line.startswith("PRINT "):
            result[target] = (positive_integer_token(line, "STRIDE"), True)
        else:
            raise ValidationError(f"unsupported FILE producer for {target}")
    if not result:
        raise ValidationError("PLUMED input declares no FILE outputs")
    return result


def read_times(path: Path) -> list[float]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValidationError(f"missing or empty PLUMED series: {path.name}")
    times: list[float] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            value = float(line.split()[0])
        except (IndexError, ValueError) as exc:
            raise ValidationError(f"{path.name}:{line_number}: invalid time") from exc
        if not math.isfinite(value):
            raise ValidationError(f"{path.name}:{line_number}: non-finite time")
        times.append(value)
    if not times:
        raise ValidationError(f"PLUMED series has no data rows: {path.name}")
    return times


def validate_series(
    name: str,
    times: list[float],
    stride: int,
    includes_zero: bool,
    dt: float,
    checkpoint_time: float,
) -> None:
    interval = stride * dt
    tolerance = max(1e-6, abs(interval) * 1e-6)
    completed_intervals = math.floor((checkpoint_time + tolerance) / interval)
    expected_count = completed_intervals + (1 if includes_zero else 0)
    if expected_count < 1:
        raise ValidationError(f"checkpoint predates the first expected row of {name}")
    if len(times) != expected_count:
        raise ValidationError(
            f"{name}: expected {expected_count} rows through checkpoint, got {len(times)}"
        )
    first_multiplier = 0 if includes_zero else 1
    for index, actual in enumerate(times):
        expected = (index + first_multiplier) * interval
        if abs(actual - expected) > tolerance:
            raise ValidationError(
                f"{name}: row {index + 1} time {actual:g} does not match {expected:g}"
            )


def main() -> int:
    args = parse_args()
    if not math.isfinite(args.dt) or args.dt <= 0:
        print("ERROR: --dt must be positive and finite", file=sys.stderr)
        return 2
    if not math.isfinite(args.checkpoint_time) or args.checkpoint_time < 0:
        print("ERROR: --checkpoint-time must be finite and nonnegative", file=sys.stderr)
        return 2
    plumed = args.plumed.expanduser().resolve()
    base_dir = args.base_dir.expanduser().resolve()
    try:
        declarations = declared_series(plumed)
        for name, (stride, includes_zero) in declarations.items():
            times = read_times(base_dir / name)
            validate_series(
                name,
                times,
                stride,
                includes_zero,
                args.dt,
                args.checkpoint_time,
            )
    except (OSError, UnicodeError, ValidationError) as exc:
        print(f"ERROR: unsafe PLUMED restart: {exc}", file=sys.stderr)
        return 1
    print(
        f"OK: {len(declarations)} PLUMED series are complete, monotonic, and aligned "
        f"through checkpoint {args.checkpoint_time:g} ps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

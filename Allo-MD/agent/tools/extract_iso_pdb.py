#!/usr/bin/env python3
"""Extract OpenDX grid points beyond an isovalue into a PDB point cloud."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import re
import sys
import tempfile


class DXError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="OpenDX density grid")
    parser.add_argument("--output", required=True, type=Path, help="output PDB point cloud")
    parser.add_argument("--iso", required=True, type=float, help="isovalue threshold")
    return parser.parse_args()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def parse_dx(path: Path) -> tuple[tuple[int, int, int], tuple[float, float, float], list[tuple[float, float, float]], list[float]]:
    counts: tuple[int, int, int] | None = None
    origin: tuple[float, float, float] | None = None
    deltas: list[tuple[float, float, float]] = []
    item_count: int | None = None
    values: list[float] = []
    reading_values = False

    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if counts is None:
            match = re.search(r"\bclass\s+gridpositions\s+counts\s+(\d+)\s+(\d+)\s+(\d+)\b", line)
            if match:
                counts = tuple(int(value) for value in match.groups())  # type: ignore[assignment]
                continue
        if origin is None and line.startswith("origin "):
            fields = line.split()
            if len(fields) != 4:
                raise DXError(f"line {line_number}: malformed origin")
            origin = tuple(float(value) for value in fields[1:])  # type: ignore[assignment]
            continue
        if line.startswith("delta ") and len(deltas) < 3:
            fields = line.split()
            if len(fields) != 4:
                raise DXError(f"line {line_number}: malformed delta")
            deltas.append(tuple(float(value) for value in fields[1:]))
            continue
        if not reading_values:
            match = re.search(r"\bitems\s+(\d+)\s+data\s+follows\b", line)
            if match:
                item_count = int(match.group(1))
                reading_values = True
            continue
        if item_count is None or len(values) >= item_count:
            continue
        for token in line.split():
            if len(values) >= item_count:
                break
            try:
                value = float(token)
            except ValueError as exc:
                raise DXError(f"line {line_number}: nonnumeric grid value {token!r}") from exc
            if not math.isfinite(value):
                raise DXError(f"line {line_number}: non-finite grid value")
            values.append(value)

    if counts is None or origin is None or len(deltas) != 3 or item_count is None:
        raise DXError("missing counts, origin, three delta vectors, or data header")
    product = counts[0] * counts[1] * counts[2]
    if item_count != product:
        raise DXError(f"grid counts imply {product} values but header declares {item_count}")
    if len(values) != item_count:
        raise DXError(f"expected {item_count} grid values, parsed {len(values)}")
    return counts, origin, deltas, values


def coordinate(
    origin: tuple[float, float, float],
    deltas: list[tuple[float, float, float]],
    ix: int,
    iy: int,
    iz: int,
) -> tuple[float, float, float]:
    return tuple(
        origin[axis]
        + ix * deltas[0][axis]
        + iy * deltas[1][axis]
        + iz * deltas[2][axis]
        for axis in range(3)
    )  # type: ignore[return-value]


def main() -> int:
    args = parse_args()
    if not math.isfinite(args.iso):
        print("ERROR: --iso must be finite", file=sys.stderr)
        return 2
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file() or source.stat().st_size == 0:
        print(f"ERROR: missing or empty OpenDX input: {source}", file=sys.stderr)
        return 1
    try:
        counts, origin, deltas, values = parse_dx(source)
    except (OSError, UnicodeError, ValueError, DXError) as exc:
        print(f"ERROR: cannot parse {source}: {exc}", file=sys.stderr)
        return 1

    nx, ny, nz = counts
    selected: list[tuple[float, float, float]] = []
    for flat_index, value in enumerate(values):
        passes = value > args.iso if args.iso >= 0 else value < args.iso
        if not passes:
            continue
        ix = flat_index // (ny * nz)
        remainder = flat_index % (ny * nz)
        iy = remainder // nz
        iz = remainder % nz
        if ix >= nx:
            raise AssertionError("OpenDX flat-index mapping exceeded x dimension")
        selected.append(coordinate(origin, deltas, ix, iy, iz))
    if not selected:
        print(f"ERROR: no grid points pass isovalue {args.iso:g}", file=sys.stderr)
        return 1
    if len(selected) > 99999:
        print(
            f"ERROR: {len(selected)} selected points exceed the PDB serial-number limit",
            file=sys.stderr,
        )
        return 1

    records = [
        "REMARK OpenDX points with density "
        + (">" if args.iso >= 0 else "<")
        + f" {args.iso:g}"
    ]
    for serial, (x, y, z) in enumerate(selected, 1):
        if max(abs(x), abs(y), abs(z)) >= 10000:
            print("ERROR: coordinate exceeds PDB fixed-width range", file=sys.stderr)
            return 1
        # Keep the historical pseudo-atom convention expected by MDpocket.
        records.append(
            f"ATOM  {serial:5d}  C   PTH     1    {x:8.3f}{y:8.3f}{z:8.3f}"
            "  0.00  0.00           C  "
        )
    records.append("END")
    atomic_write(output, "\n".join(records) + "\n")
    print(f"OK: selected {len(selected)} of {len(values)} OpenDX points into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

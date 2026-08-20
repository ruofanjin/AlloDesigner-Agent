#!/usr/bin/env python3
"""Create a numerically ordered, relocatable MDpocket PDB snapshot list."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import re
import sys
import tempfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--relative-to",
        type=Path,
        help="base directory for paths written to the list (default: output directory)",
    )
    parser.add_argument("--prefix", default="frame", help="frame filename prefix (default: frame)")
    parser.add_argument("--expected-count", type=int)
    parser.add_argument(
        "--expected-atoms",
        type=int,
        help="require exactly this many ATOM records and one END/ENDMDL per PDB",
    )
    parser.add_argument(
        "--frame-interval-ps",
        type=float,
        help="validate TITLE t= against zero-based frame index times this interval",
    )
    return parser.parse_args()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    args = parse_args()
    if args.expected_count is not None and args.expected_count < 1:
        print("ERROR: --expected-count must be positive", file=sys.stderr)
        return 2
    if args.expected_atoms is not None and args.expected_atoms < 1:
        print("ERROR: --expected-atoms must be positive", file=sys.stderr)
        return 2
    if args.frame_interval_ps is not None and args.frame_interval_ps <= 0:
        print("ERROR: --frame-interval-ps must be positive", file=sys.stderr)
        return 2
    frames_dir = args.frames_dir.expanduser().resolve()
    output = args.output.expanduser().resolve()
    relative_to = (
        args.relative_to.expanduser().resolve()
        if args.relative_to is not None
        else output.parent
    )
    if not frames_dir.is_dir():
        print(f"ERROR: frames directory does not exist: {frames_dir}", file=sys.stderr)
        return 1

    expression = re.compile(rf"^{re.escape(args.prefix)}(\d+)\.pdb$")
    indexed: dict[int, Path] = {}
    unexpected: list[str] = []
    for path in frames_dir.glob("*.pdb"):
        match = expression.fullmatch(path.name)
        if not match:
            unexpected.append(path.name)
            continue
        number = int(match.group(1))
        if number in indexed:
            print(f"ERROR: duplicate numeric frame index {number}", file=sys.stderr)
            return 1
        if not path.is_file() or path.stat().st_size == 0:
            print(f"ERROR: missing or empty frame: {path}", file=sys.stderr)
            return 1
        if args.expected_atoms is not None:
            atom_count = 0
            terminator_count = 0
            title_times: list[float] = []
            last_nonempty = ""
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    stripped = line.rstrip()
                    if stripped:
                        last_nonempty = stripped
                    if line.startswith("TITLE"):
                        time_match = re.search(
                            r"\bt\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)",
                            line,
                        )
                        if time_match:
                            title_times.append(float(time_match.group(1)))
                    if line.startswith("ATOM"):
                        atom_count += 1
                        try:
                            coordinates = tuple(float(line[start:end]) for start, end in ((30, 38), (38, 46), (46, 54)))
                        except ValueError:
                            print(f"ERROR: invalid ATOM coordinates in {path}", file=sys.stderr)
                            return 1
                        if not all(math.isfinite(value) for value in coordinates):
                            print(f"ERROR: non-finite ATOM coordinates in {path}", file=sys.stderr)
                            return 1
                    if stripped in {"END", "ENDMDL"}:
                        terminator_count += 1
            if atom_count != args.expected_atoms or terminator_count != 1 or last_nonempty != "ENDMDL":
                print(
                    f"ERROR: incomplete frame {path}: ATOM={atom_count} "
                    f"(expected {args.expected_atoms}), END/ENDMDL={terminator_count} "
                    f"(expected 1), last={last_nonempty!r} (expected 'ENDMDL')",
                    file=sys.stderr,
                )
                return 1
            if args.frame_interval_ps is not None:
                expected_time = number * args.frame_interval_ps
                if (
                    len(title_times) != 1
                    or not math.isfinite(title_times[0])
                    or abs(title_times[0] - expected_time) > 1e-3
                ):
                    print(
                        f"ERROR: frame {number} TITLE time {title_times!r}; "
                        f"expected {expected_time} ps",
                        file=sys.stderr,
                    )
                    return 1
        indexed[number] = path.resolve()
    if unexpected:
        print(
            f"ERROR: unexpected PDB names in {frames_dir}: {', '.join(sorted(unexpected))}",
            file=sys.stderr,
        )
        return 1
    if not indexed:
        print(f"ERROR: no {args.prefix}<integer>.pdb files in {frames_dir}", file=sys.stderr)
        return 1

    indices = sorted(indexed)
    expected_indices = list(range(len(indices)))
    if indices != expected_indices:
        missing = sorted(set(range(indices[-1] + 1)) - set(indices))
        print(
            "ERROR: frame indices must be contiguous and start at 0; "
            f"found {indices[0]}..{indices[-1]}, missing {missing[:20]}",
            file=sys.stderr,
        )
        return 1
    if args.expected_count is not None and len(indices) != args.expected_count:
        print(
            f"ERROR: expected {args.expected_count} frames (0..{args.expected_count - 1}), "
            f"got {len(indices)} (0..{indices[-1]})",
            file=sys.stderr,
        )
        return 1

    lines = [os.path.relpath(indexed[number], relative_to) for number in indices]
    if any(Path(line).is_absolute() for line in lines):
        print("ERROR: failed to construct relative snapshot paths", file=sys.stderr)
        return 1
    atomic_write(output, "\n".join(lines) + "\n")
    print(
        f"OK: wrote {len(lines)} snapshots (frame0..frame{indices[-1]}) to {output}; "
        "MDpocket snapshot 1 corresponds to frame0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

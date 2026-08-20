#!/usr/bin/env python3
"""Validate MDpocket descriptors and export an off-by-one-safe volume trace."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import sys
import tempfile


class DescriptorError(RuntimeError):
    pass


HISTORICAL_HEADER = (
    "snapshot pock_volume pock_asa pock_pol_asa pock_apol_asa pock_asa22 "
    "pock_pol_asa22 pock_apol_asa22 nb_AS mean_as_ray mean_as_solv_acc "
    "apol_as_prop mean_loc_hyd_dens hydrophobicity_score volume_score "
    "polarity_score charge_score prop_polar_atm as_density as_max_dst "
    "convex_hull_volume nb_abpa ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE "
    "LEU LYS MET PHE PRO SER THR TRP TYR VAL"
).split()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--csv-output", required=True, type=Path)
    parser.add_argument(
        "--qc-output",
        type=Path,
        help="optional machine-readable JSON validation report",
    )
    parser.add_argument("--output", type=Path, help="optional PNG; skipped if matplotlib is absent")
    parser.add_argument("--frame-interval-ps", required=True, type=float)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument(
        "--require-historical-schema",
        action="store_true",
        help="require the archived 42-column MDpocket descriptor header",
    )
    return parser.parse_args()


def read_descriptors(
    path: Path, require_historical_schema: bool
) -> tuple[list[tuple[int, float]], list[str], dict[str, int]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise DescriptorError("file is empty")
    header = lines[0].split()
    if len(header) != len(set(header)):
        raise DescriptorError("header contains duplicate column names")
    if require_historical_schema and header != HISTORICAL_HEADER:
        raise DescriptorError(
            "descriptor header does not match the archived 42-column MDpocket schema"
        )
    for required in ("snapshot", "pock_volume"):
        if required not in header:
            raise DescriptorError(f"required column {required!r} is missing")
    snapshot_column = header.index("snapshot")
    volume_column = header.index("pock_volume")
    nonfinite_by_column = {name: 0 for name in header}
    values: list[tuple[int, float]] = []
    for line_number, line in enumerate(lines[1:], 2):
        fields = line.split()
        if len(fields) != len(header):
            raise DescriptorError(
                f"line {line_number}: expected {len(header)} fields, got {len(fields)}"
            )
        try:
            numeric_fields = [float(field) for field in fields]
        except ValueError as exc:
            raise DescriptorError(f"line {line_number}: nonnumeric descriptor value") from exc
        for column, value in zip(header, numeric_fields):
            if not math.isfinite(value):
                nonfinite_by_column[column] += 1
        snapshot_float = numeric_fields[snapshot_column]
        volume = numeric_fields[volume_column]
        if not math.isfinite(snapshot_float) or not snapshot_float.is_integer() \
                or snapshot_float < 1:
            raise DescriptorError(
                f"line {line_number}: snapshot must be a finite positive integer"
            )
        if not math.isfinite(volume) or volume < 0:
            raise DescriptorError(f"line {line_number}: pock_volume must be finite and nonnegative")
        values.append((int(snapshot_float), volume))
    if not values:
        raise DescriptorError("no descriptor rows")
    values.sort()
    snapshots = [snapshot for snapshot, _ in values]
    if len(snapshots) != len(set(snapshots)):
        raise DescriptorError("duplicate snapshot ids")
    expected = list(range(1, len(snapshots) + 1))
    if snapshots != expected:
        missing = sorted(set(range(1, snapshots[-1] + 1)) - set(snapshots))
        raise DescriptorError(
            "snapshots must be contiguous and start at 1; "
            f"found {snapshots[0]}..{snapshots[-1]}, missing {missing[:20]}"
        )
    return values, header, {
        column: count for column, count in nonfinite_by_column.items() if count
    }


def write_csv_atomic(path: Path, rows: list[tuple[int, int, float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(("snapshot", "frame_index", "time_ps", "pock_volume_A3"))
            writer.writerows(rows)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def save_plot(path: Path, rows: list[tuple[int, int, float, float]]) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("NOTICE: matplotlib is unavailable; validated CSV written, PNG skipped", file=sys.stderr)
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.", suffix=path.suffix or ".png", dir=path.parent
    )
    os.close(descriptor)
    try:
        figure, axis = plt.subplots(figsize=(12, 4))
        axis.plot([row[2] for row in rows], [row[3] for row in rows])
        axis.set_xlabel("Time (ps)")
        axis.set_ylabel("Pocket volume (A^3)")
        axis.set_title("Pocket Volume Over Time")
        axis.grid(True)
        figure.tight_layout()
        figure.savefig(temporary_name, dpi=300)
        plt.close(figure)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return True


def main() -> int:
    args = parse_args()
    if not math.isfinite(args.frame_interval_ps) or args.frame_interval_ps <= 0:
        print("ERROR: --frame-interval-ps must be positive and finite", file=sys.stderr)
        return 2
    if args.expected_count is not None and args.expected_count < 1:
        print("ERROR: --expected-count must be positive", file=sys.stderr)
        return 2
    source = args.input.expanduser().resolve()
    if not source.is_file() or source.stat().st_size == 0:
        print(f"ERROR: missing or empty descriptor file: {source}", file=sys.stderr)
        return 1
    try:
        descriptors, header, nonfinite_by_column = read_descriptors(
            source, args.require_historical_schema
        )
    except (OSError, UnicodeError, DescriptorError) as exc:
        print(f"ERROR: invalid MDpocket descriptors: {exc}", file=sys.stderr)
        return 1
    if args.expected_count is not None and len(descriptors) != args.expected_count:
        print(
            f"ERROR: expected {args.expected_count} descriptor rows, got {len(descriptors)}",
            file=sys.stderr,
        )
        return 1

    # MDpocket numbers snapshots from 1, while gmx -sep names frames from 0.
    # Therefore snapshot 1 -> frame_index 0 -> time 0 ps.
    rows = [
        (snapshot, snapshot - 1, (snapshot - 1) * args.frame_interval_ps, volume)
        for snapshot, volume in descriptors
    ]
    csv_path = args.csv_output.expanduser().resolve()
    write_csv_atomic(csv_path, rows)
    qc_path = args.qc_output.expanduser().resolve() if args.qc_output is not None else None
    if qc_path is not None:
        volumes = [volume for _, volume in descriptors]
        write_json_atomic(
            qc_path,
            {
                "schema_version": 1,
                "descriptor_schema": header,
                "historical_schema_required": args.require_historical_schema,
                "row_count": len(rows),
                "snapshot": {
                    "first": rows[0][0],
                    "last": rows[-1][0],
                    "contiguous_from_one": True,
                },
                "frame": {
                    "first_index": rows[0][1],
                    "last_index": rows[-1][1],
                    "interval_ps": args.frame_interval_ps,
                    "first_time_ps": rows[0][2],
                    "last_time_ps": rows[-1][2],
                },
                "pock_volume_A3": {
                    "minimum": min(volumes),
                    "maximum": max(volumes),
                    "zero_count": sum(volume == 0 for volume in volumes),
                },
                "nonfinite": {
                    "total": sum(nonfinite_by_column.values()),
                    "by_column": nonfinite_by_column,
                },
                "validation_policy": {
                    "snapshot": "finite positive integer; unique and contiguous from 1",
                    "pock_volume": "finite and nonnegative",
                    "other_descriptors": (
                        "nonnumeric values are rejected; non-finite numeric values are retained "
                        "in the source and counted here; no interpolation or imputation"
                    ),
                },
            },
        )
    plotted = False
    if args.output is not None:
        try:
            plotted = save_plot(args.output.expanduser().resolve(), rows)
        except Exception as exc:
            print(
                f"NOTICE: optional matplotlib plot failed; mandatory CSV/QC remain valid: {exc}",
                file=sys.stderr,
            )
    suffix = f"; PNG written to {args.output.expanduser().resolve()}" if plotted else ""
    qc_suffix = f"; QC written to {qc_path}" if qc_path is not None else ""
    print(
        f"OK: {len(rows)} rows; snapshot 1 = frame0 = 0 ps; CSV written to {csv_path}"
        f"{qc_suffix}; non-finite auxiliary values={sum(nonfinite_by_column.values())}{suffix}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

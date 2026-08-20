#!/usr/bin/env python3
"""Select isosurface grid points within a cutoff of specified PDB residues."""

from __future__ import annotations

import argparse
from collections import defaultdict
import math
import os
from pathlib import Path
import sys
import tempfile


class PDBError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid", required=True, type=Path, help="PDB point cloud")
    parser.add_argument("--reference", required=True, type=Path, help="aligned protein PDB")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--residues",
        required=True,
        help="comma-separated residue ids/ranges, e.g. 354,355,410-417",
    )
    parser.add_argument("--cutoff", required=True, type=float, help="distance cutoff in Angstrom")
    return parser.parse_args()


def parse_residues(specification: str) -> set[int]:
    residues: set[int] = set()
    for raw in specification.split(","):
        item = raw.strip()
        if not item:
            raise ValueError("empty residue item")
        if "-" in item:
            fields = item.split("-", 1)
            if len(fields) != 2:
                raise ValueError(f"invalid residue range {item!r}")
            first, last = (int(field) for field in fields)
            if first > last:
                raise ValueError(f"descending residue range {item!r}")
            residues.update(range(first, last + 1))
        else:
            residues.add(int(item))
    if not residues:
        raise ValueError("no residues specified")
    return residues


def pdb_atoms(path: Path) -> list[tuple[int, float, float, float]]:
    atoms: list[tuple[int, float, float, float]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.startswith(("ATOM  ", "HETATM")):
            continue
        if len(raw) < 54:
            raise PDBError(f"{path.name}:{line_number}: coordinate record is too short")
        try:
            residue = int(raw[22:26])
            x = float(raw[30:38])
            y = float(raw[38:46])
            z = float(raw[46:54])
        except ValueError as exc:
            raise PDBError(f"{path.name}:{line_number}: invalid fixed-width coordinate") from exc
        if not all(math.isfinite(value) for value in (x, y, z)):
            raise PDBError(f"{path.name}:{line_number}: non-finite coordinate")
        atoms.append((residue, x, y, z))
    if not atoms:
        raise PDBError(f"{path}: no ATOM/HETATM records")
    return atoms


def bin_key(x: float, y: float, z: float, cell: float) -> tuple[int, int, int]:
    return (math.floor(x / cell), math.floor(y / cell), math.floor(z / cell))


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


def main() -> int:
    args = parse_args()
    if not math.isfinite(args.cutoff) or args.cutoff <= 0:
        print("ERROR: --cutoff must be a positive finite Angstrom value", file=sys.stderr)
        return 2
    try:
        residues = parse_residues(args.residues)
    except ValueError as exc:
        print(f"ERROR: invalid --residues value: {exc}", file=sys.stderr)
        return 2

    grid_path = args.grid.expanduser().resolve()
    reference_path = args.reference.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    try:
        grid_atoms = pdb_atoms(grid_path)
        reference_atoms = pdb_atoms(reference_path)
    except (OSError, UnicodeError, PDBError) as exc:
        print(f"ERROR: cannot read PDB input: {exc}", file=sys.stderr)
        return 1

    target_atoms = [atom[1:] for atom in reference_atoms if atom[0] in residues]
    present_residues = {atom[0] for atom in reference_atoms if atom[0] in residues}
    missing_residues = sorted(residues - present_residues)
    if missing_residues:
        print(
            f"ERROR: requested residues absent from reference: {missing_residues}",
            file=sys.stderr,
        )
        return 1
    if not target_atoms:
        print("ERROR: selected residues contain no reference atoms", file=sys.stderr)
        return 1

    bins: dict[tuple[int, int, int], list[tuple[float, float, float]]] = defaultdict(list)
    for x, y, z in target_atoms:
        bins[bin_key(x, y, z, args.cutoff)].append((x, y, z))
    cutoff_squared = args.cutoff * args.cutoff
    selected: list[tuple[float, float, float]] = []
    for _, x, y, z in grid_atoms:
        bx, by, bz = bin_key(x, y, z, args.cutoff)
        close = False
        for dx in (-1, 0, 1):
            if close:
                break
            for dy in (-1, 0, 1):
                if close:
                    break
                for dz in (-1, 0, 1):
                    for tx, ty, tz in bins.get((bx + dx, by + dy, bz + dz), ()):
                        squared = (x - tx) ** 2 + (y - ty) ** 2 + (z - tz) ** 2
                        if squared <= cutoff_squared:
                            close = True
                            break
                    if close:
                        break
        if close:
            selected.append((x, y, z))
    if not selected:
        print(
            f"ERROR: no grid points are within {args.cutoff:g} Angstrom of target residues",
            file=sys.stderr,
        )
        return 1
    if len(selected) > 99999:
        print("ERROR: selected point count exceeds PDB serial-number limit", file=sys.stderr)
        return 1

    records = [
        f"REMARK Grid points within {args.cutoff:g} A of residues "
        + ",".join(str(residue) for residue in sorted(residues))
    ]
    for serial, (x, y, z) in enumerate(selected, 1):
        # MDpocket's selected-pocket input historically uses ATOM/PTH points.
        records.append(
            f"ATOM  {serial:5d}  C   PTH     1    {x:8.3f}{y:8.3f}{z:8.3f}"
            "  0.00  0.00           C  "
        )
    records.append("END")
    atomic_write(output_path, "\n".join(records) + "\n")
    print(
        f"OK: selected {len(selected)} of {len(grid_atoms)} grid points near "
        f"{len(target_atoms)} atoms in {len(residues)} residues"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

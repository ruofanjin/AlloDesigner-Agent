#!/usr/bin/env python3
"""Validate immutable GLP1 workflow inputs before any expensive calculation.

Only Python's standard library is used so this check also works on a freshly
provisioned host.  ``--inputs-root`` may point at an Agent run's copied input
snapshot; when omitted, the bundle's own ``inputs`` directory is checked.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys
from typing import Callable


EXPECTED_HASHES = {
    "mdp/chi/chi_metad_10ns.mdp": "68ed0dce080ec9a50593a0aefbd8e9dd6f5ec7a0c610f0501febb164c99b6b46",
    "mdp/chi/chi_monitor_10ns.mdp": "68ed0dce080ec9a50593a0aefbd8e9dd6f5ec7a0c610f0501febb164c99b6b46",
    "mdp/distance/distance_metad_100ns_new_bias.mdp": "2c47131cd788977daed649d2fbaafbde8e5c8630f51f52c7bbb2ece8ade6cc42",
    "mdp/distance/distance_metad_50ns.mdp": "b27724a0962bcd83dccf418c9f9a71286e20828176609f722a994b6e0a55b032",
    "mdp/distance/distance_monitor_50ns.mdp": "152b90379cd0eb8aff2ce7fc6684f350db2b63f8151747761b0cda3a687a528f",
    "mdp/equilibration/step6.0_minimization.mdp": "fbf84b1cd5970cfa2e7c64f63d61a43435245bc0e2f03df14ab70bcaa1818119",
    "mdp/equilibration/step6.1_equilibration.mdp": "9776cba49f8a86d87a6e337e7cbbd343059c554c3714a9213f564d18d369a101",
    "mdp/equilibration/step6.2_equilibration.mdp": "91a737c87e6870eb8d7911c33a27b4a5f08b035645fc1be033eecc7bac90b181",
    "mdp/equilibration/step6.3_equilibration.mdp": "c93afa6ddef7d2f147222790db37b6b54abd0e922ea915241070defab626b765",
    "mdp/equilibration/step6.4_equilibration.mdp": "7259ab5e713f583f428a6a922c1694a3f86cd1096ba32f350edd1191489a6357",
    "mdp/equilibration/step6.5_equilibration.mdp": "6aee4d9ae12de9e2a5444d956f85e042443f4188ca29c485c5b287c7232e9839",
    "mdp/equilibration/step6.6_equilibration.mdp": "a903850f21b161b51a4559a362e82d35fb2acc9da65dfa126e1ff777288be846",
    "mdp/normal/step7.1_production.mdp": "214c88d622f69d996cf5d402b17e16b46977a7cce51a557e1620569a2fb1c2b7",
    "mdp/normal/step7.2_production.mdp": "11b787b66a5c7b7ccbaaa5e5078ad8a1ffa707091dc5f2348a1efb9e765e7dd8",
    "mdp/normal/step7.3_production.mdp": "ddef07f7f49b96544d624da8831477a2ab119459d71638875051511bb83ff08b",
    "mdp/normal/step7.4_production.mdp": "088eb5111c0e57bcdd31817594a196c0ed3c0ce840024202195e0a208f331b54",
    "mdp/sasa/sasa_pocket_100ns.mdp": "d14c4fbaaaf6367ba101e464808fe241a48cc4019df696db2e818fc5df51e7aa",
    "mdp/sasa/sasa_pocket_10ns.mdp": "ae6f81b0bb0f646271792f0e95ed154bf1987a9dc31bbfcf41139f57e47f4bdc",
    "mdp/sasa/sasa_pocket_1ns.mdp": "ab6e0e280fce9754c72645cd1e4c3b602a31d9b7dcb8650344e19a6dc0e853c6",
    "mdp/sasa/sasa_site_10ns.mdp": "ae6f81b0bb0f646271792f0e95ed154bf1987a9dc31bbfcf41139f57e47f4bdc",
    "mdp/sasa/sasa_site_1ns.mdp": "ab6e0e280fce9754c72645cd1e4c3b602a31d9b7dcb8650344e19a6dc0e853c6",
    "plumed/chi/chi_metad.dat": "972d3199967698c7ea3e0e9009cf6dedabf00d3fb049e53d992d41d67be77165",
    "plumed/chi/chi_monitor.dat": "d582e3845d966424ec5b8c9659a6e22c8c453729801aaa44745ba48cb2ce7e2e",
    "system/step5_input.gro": "e18742142a3d806c7e922af1643fc6bf3dee2cc009bc4a0a9406de553cfc1db1",
    "system/step5_input3.pdb": "7ff7c25fafeb202439dc646a32fd42012375ffa591ffe6e74127419971ea23ea",
    "system/topol.top": "656afae913139016223d5b56e535931b006bf2b7e3bb3cac603d46d2102967d3",
    "system/index.ndx": "fec9505bba8278de01e4933aed3877b7a809cffd7bc3148003f914e23214c056",
    "plumed/distance_monitor/distance_monitor.dat": "a8a3169ba3e45c64a90dc3329113749b3ba80fb2bfd48223be202af72b25a762",
    "plumed/distance_metad/distance_metad.dat": "eb3a9d04d56a8857227ce23b3f62628087258a4fc15ca84842d0cf986e789af8",
    "plumed/sasa_site/sasa_site.dat": "39574d30f8688dd2fae36b6a5df6e3c430f3d172c54f584c7794dcde6fc40e10",
    "plumed/sasa_pocket_8A/sasa_pocket_8A.dat": "53f0292ad72837b0f1a2f0d0babcc10ecd156f33dce98ed722174806174f39f3",
    "analysis/5vex_holo_convert_apo_id_allosteric_site_2A.pdb": "95072f6600a0f09491ca9f6cb31e1f2a0f1d46285fd14e5b4ec9133671878563",
    "analysis/allosteric_all_atoms_2A.ndx": "ccb48cb40f4be248effd5100ce4a17899ae75ebfe674743d8bb884a10375d831",
    "analysis/allosteric_backbone_2A.ndx": "2a94bcf4728b85258f7eb787ba504552b4e1d3c5019126f16deeb8d6bf1efe24",
    "analysis/protein_backbone.ndx": "1fc2391c7d5fdc234122d4827f4f8d560697a8de87bb1e8146929b561753ba95",
    "analysis/tm6_ecl3_tm7_backbone.ndx": "31415637c4eecbbd42019e3a5ead1885f1a5ccf455d11722673baa88c1f79a12",
    "analysis/tm6_tm7_backbone.ndx": "336a5c80bb3bd9132325bb5a6c9b7842e3e837127f75db65f5df7394f9dabdd0",
    "system/toppar/Cl-.itp": "9a5655be897de1ecd31700684d16a55da33499acd1505b8f97aaa26e7a124162",
    "system/toppar/K+.itp": "870c920636dd793e0cbc59adf9e82bac549183bd8611ad336e1fea4633f2fa79",
    "system/toppar/POPC.itp": "a740ab64bb88abfbf75b47f6d7a8e1e68b97f39d0da56032b55d09dcdc98ef12",
    "system/toppar/PROA.itp": "b66aecd67fe487930764d17e589c80a8b7b964dd84b9c7a98c772d5b825b287a",
    "system/toppar/PROB.itp": "835434aaf58b9b65754018fe035931534bf0ea0d16927d3cc247b3c9ab59e2db",
    "system/toppar/PROC.itp": "c158b1084ec18a57dcf8f43dd2d845a5bf27d64553a189762f5857d7f0a307f5",
    "system/toppar/PROD.itp": "57024147f92d24cd8ff98174284ac24a096067a683c44805b26ad680e26e6703",
    "system/toppar/TP3.itp": "9dad688dd63f7e73c0f39571b601aceaedc56ca98e32b222c76c0790f890b6ee",
    "system/toppar/forcefield.itp": "37185ade8291ae1433c7f8cda22e58b4db9f65f1618399387803c19ea14271db",
    "mdp/normal/step7_1ns_demo.mdp": "9d544bbe6f1c4f95624a67fa0327aeaa9ca5a97037811c81589a905dc4677887",
    "mdp/distance/distance_monitor_1ns_demo.mdp": "9d544bbe6f1c4f95624a67fa0327aeaa9ca5a97037811c81589a905dc4677887",
    "mdp/distance/distance_metad_1ns_demo.mdp": "9d544bbe6f1c4f95624a67fa0327aeaa9ca5a97037811c81589a905dc4677887",
}

EXPECTED_NDX = {
    "system/index.ndx": {
        "SOLU": 7952,
        "MEMB": 51322,
        "SOLV": 178109,
        "SOLU_MEMB": 59274,
        "SYSTEM": 237383,
    },
    "analysis/protein_backbone.ndx": {"Backbone": 1473},
    "analysis/tm6_ecl3_tm7_backbone.ndx": {"Backbone": 183},
    "analysis/tm6_tm7_backbone.ndx": {"Backbone": 144},
    "analysis/allosteric_all_atoms_2A.ndx": {"Protein": 337},
    "analysis/allosteric_backbone_2A.ndx": {"Backbone": 60},
}

EXPECTED_MOLECULES = {
    "PROA": 1,
    "PROB": 1,
    "PROC": 1,
    "PROD": 1,
    "POPC": 383,
    "K+": 161,
    "Cl-": 162,
    "TP3": 59262,
}

EXPECTED_INCLUDES = {
    "toppar/forcefield.itp",
    "toppar/PROA.itp",
    "toppar/PROB.itp",
    "toppar/PROC.itp",
    "toppar/PROD.itp",
    "toppar/POPC.itp",
    "toppar/K+.itp",
    "toppar/Cl-.itp",
    "toppar/TP3.itp",
}

LEFT_ATOMS = (5761, 5780, 5813, 5837, 5946, 6017)
RIGHT_ATOMS = (6678, 6697, 6721, 6732, 6752, 6768, 6782, 6796)
DISTANCE_LABELS = tuple(f"d{number}" for number in range(1, 49))


class ValidationError(RuntimeError):
    """A concise, user-facing validation failure."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_file(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.is_file():
        raise ValidationError(f"missing file: {relative}")
    if path.stat().st_size == 0:
        raise ValidationError(f"empty file: {relative}")
    return path


def validate_hashes(root: Path) -> None:
    mismatches: list[str] = []
    for relative, expected in EXPECTED_HASHES.items():
        path = require_file(root, relative)
        actual = sha256(path)
        if actual != expected:
            mismatches.append(f"{relative}: expected {expected}, got {actual}")
    if mismatches:
        raise ValidationError("SHA-256 mismatch:\n  " + "\n  ".join(mismatches))


def parse_ndx(path: Path) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    current: str | None = None
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        header = re.fullmatch(r"\[\s*(.+?)\s*\]", line)
        if header:
            current = header.group(1)
            if current in groups:
                raise ValidationError(f"{path.name}:{line_number}: duplicate group {current!r}")
            groups[current] = []
            continue
        if current is None:
            raise ValidationError(f"{path.name}:{line_number}: atom ids before a group header")
        for token in line.split():
            if not token.isdigit() or int(token) < 1:
                raise ValidationError(f"{path.name}:{line_number}: invalid atom id {token!r}")
            groups[current].append(int(token))
    return groups


def validate_atom_counts(root: Path) -> None:
    gro = require_file(root, "system/step5_input.gro")
    with gro.open("rt", encoding="utf-8") as handle:
        handle.readline()
        atom_line = handle.readline().strip()
    try:
        gro_atoms = int(atom_line)
    except ValueError as exc:
        raise ValidationError("system/step5_input.gro: line 2 is not an atom count") from exc
    if gro_atoms != 237383:
        raise ValidationError(f"system/step5_input.gro: expected 237383 atoms, got {gro_atoms}")

    pdb_expectations = {
        "system/step5_input3.pdb": 7952,
        "analysis/5vex_holo_convert_apo_id_allosteric_site_2A.pdb": 60,
    }
    for relative, expected in pdb_expectations.items():
        path = require_file(root, relative)
        count = sum(
            1
            for line in path.read_text(encoding="utf-8", errors="strict").splitlines()
            if line.startswith(("ATOM  ", "HETATM"))
        )
        if count != expected:
            raise ValidationError(f"{relative}: expected {expected} coordinate atoms, got {count}")

    for relative, expected_groups in EXPECTED_NDX.items():
        groups = parse_ndx(require_file(root, relative))
        if set(groups) != set(expected_groups):
            raise ValidationError(
                f"{relative}: expected groups {sorted(expected_groups)}, got {sorted(groups)}"
            )
        for name, expected_count in expected_groups.items():
            atoms = groups[name]
            if len(atoms) != expected_count:
                raise ValidationError(
                    f"{relative} [{name}]: expected {expected_count} atoms, got {len(atoms)}"
                )
            if len(atoms) != len(set(atoms)):
                raise ValidationError(f"{relative} [{name}]: duplicate atom ids")
            if max(atoms) > gro_atoms:
                raise ValidationError(f"{relative} [{name}]: atom id exceeds {gro_atoms}")


def validate_topology(root: Path) -> None:
    path = require_file(root, "system/topol.top")
    text = path.read_text(encoding="utf-8")
    includes = set(re.findall(r'^\s*#include\s+"([^"]+)"', text, flags=re.MULTILINE))
    if includes != EXPECTED_INCLUDES:
        raise ValidationError(
            "system/topol.top: include set differs; expected "
            f"{sorted(EXPECTED_INCLUDES)}, got {sorted(includes)}"
        )
    section: str | None = None
    molecules: dict[str, int] = {}
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        header = re.fullmatch(r"\[\s*(.+?)\s*\]", line)
        if header:
            section = header.group(1).lower()
            continue
        if section == "molecules":
            fields = line.split()
            if len(fields) != 2 or not fields[1].isdigit():
                raise ValidationError(f"system/topol.top: malformed molecule line {line!r}")
            if fields[0] in molecules:
                raise ValidationError(f"system/topol.top: duplicate molecule {fields[0]!r}")
            molecules[fields[0]] = int(fields[1])
    if molecules != EXPECTED_MOLECULES:
        raise ValidationError(
            f"system/topol.top: molecule table differs; expected {EXPECTED_MOLECULES}, got {molecules}"
        )


def distance_definitions(text: str) -> list[tuple[str, int, int]]:
    matches = re.findall(
        r"^\s*(d\d+):\s+DISTANCE\s+ATOMS=(\d+),(\d+)\s*$",
        text,
        flags=re.MULTILINE,
    )
    return [(label, int(left), int(right)) for label, left, right in matches]


def require_distance_basis(relative: str, text: str) -> None:
    expected_pairs = [(left, right) for left in LEFT_ATOMS for right in RIGHT_ATOMS]
    definitions = distance_definitions(text)
    if [entry[0] for entry in definitions] != list(DISTANCE_LABELS):
        raise ValidationError(f"{relative}: DISTANCE labels must be exactly d1..d48 in order")
    if [(entry[1], entry[2]) for entry in definitions] != expected_pairs:
        raise ValidationError(f"{relative}: 48-distance atom-pair Cartesian product differs")
    if "MOLINFO MOLTYPE=protein STRUCTURE=step5_input3.pdb" not in text:
        raise ValidationError(f"{relative}: MOLINFO reference is not step5_input3.pdb")


def csv_argument(text: str, key: str) -> list[str]:
    match = re.search(rf"\b{re.escape(key)}=([^\s]+)", text)
    return match.group(1).split(",") if match else []


def validate_distance_dat(root: Path) -> None:
    monitor_rel = "plumed/distance_monitor/distance_monitor.dat"
    monitor = require_file(root, monitor_rel).read_text(encoding="utf-8")
    require_distance_basis(monitor_rel, monitor)
    upper = monitor.upper()
    if any(keyword in upper for keyword in ("METAD", "BIASVALUE", "COMBINE")):
        raise ValidationError(f"{monitor_rel}: monitor must not define a bias or COMBINE")
    print_line = next((line for line in monitor.splitlines() if line.strip().startswith("PRINT ")), "")
    if csv_argument(print_line, "ARG") != list(DISTANCE_LABELS):
        raise ValidationError(f"{monitor_rel}: PRINT ARG must be exactly d1..d48")
    if not re.search(r"\bSTRIDE=500\b", print_line) or not re.search(
        r"\bFILE=colvar_distance\b", print_line
    ):
        raise ValidationError(f"{monitor_rel}: PRINT must use STRIDE=500 FILE=colvar_distance")

    metad_rel = "plumed/distance_metad/distance_metad.dat"
    metad = require_file(root, metad_rel).read_text(encoding="utf-8")
    require_distance_basis(metad_rel, metad)
    if "BIASVALUE" in metad.upper():
        raise ValidationError(f"{metad_rel}: unexpected BIASVALUE would double the metadynamics bias")
    for label in ("sigma1", "sigma2"):
        match = re.search(rf"^\s*{label}:\s+COMBINE\s+(.+)$", metad, flags=re.MULTILINE)
        if not match:
            raise ValidationError(f"{metad_rel}: missing {label} COMBINE")
        body = match.group(1)
        if csv_argument(body, "ARG") != list(DISTANCE_LABELS):
            raise ValidationError(f"{metad_rel}: {label} ARG must be exactly d1..d48")
        coefficients = csv_argument(body, "COEFFICIENTS")
        if len(coefficients) != 48:
            raise ValidationError(f"{metad_rel}: {label} must have 48 coefficients")
        try:
            [float(value) for value in coefficients]
        except ValueError as exc:
            raise ValidationError(f"{metad_rel}: {label} has a nonnumeric coefficient") from exc
    compact = re.sub(r"\s+", " ", metad)
    required_metad_tokens = (
        "ARG=sigma1,sigma2",
        "PACE=500",
        "HEIGHT=5.000000",
        "TEMP=310",
        "BIASFACTOR=10",
        "SIGMA=0.732663,0.732663",
        "FILE=HILLS",
    )
    metad_delimiters = re.findall(
        r"^\s*(?:METAD\s+\.\.\.|\.\.\.\s+METAD)\s*$", metad, flags=re.MULTILINE
    )
    if len(metad_delimiters) != 2 or not all(token in compact for token in required_metad_tokens):
        raise ValidationError(f"{metad_rel}: METAD block parameters differ")
    print_line = next((line for line in metad.splitlines() if line.strip().startswith("PRINT ")), "")
    expected_print = list(DISTANCE_LABELS) + ["sigma1", "sigma2", "metad.rbias"]
    if csv_argument(print_line, "ARG") != expected_print:
        raise ValidationError(f"{metad_rel}: PRINT columns differ")
    if "FILE=COLVAR_biased.dat" not in print_line or "STRIDE=500" not in print_line:
        raise ValidationError(f"{metad_rel}: PRINT output or stride differs")


def expand_atom_ranges(specification: str) -> list[int]:
    result: list[int] = []
    for item in specification.split(","):
        if "-" in item:
            first_text, last_text = item.split("-", 1)
            first, last = int(first_text), int(last_text)
            if first > last:
                raise ValidationError(f"descending atom range {item!r}")
            result.extend(range(first, last + 1))
        else:
            result.append(int(item))
    return result


def validate_sasa_dat(root: Path) -> None:
    cases = (
        ("plumed/sasa_site/sasa_site.dat", 254, True),
        ("plumed/sasa_pocket_8A/sasa_pocket_8A.dat", 648, False),
    )
    for relative, expected_count, excluded_oxt in cases:
        text = require_file(root, relative).read_text(encoding="utf-8")
        match = re.search(r"\bSASA_HASEL\b[^\n]*\bATOMS=([0-9,\-]+)", text)
        if not match:
            raise ValidationError(f"{relative}: missing SASA_HASEL ATOMS")
        atoms = expand_atom_ranges(match.group(1).strip(","))
        if len(atoms) != expected_count or len(atoms) != len(set(atoms)):
            raise ValidationError(
                f"{relative}: expected {expected_count} unique SASA atoms, got {len(atoms)}"
            )
        if excluded_oxt and 6716 in atoms:
            raise ValidationError(f"{relative}: terminal OXT atom 6716 must remain excluded")
        compact = re.sub(r"\s+", " ", text)
        metad_delimiters = re.findall(
            r"^\s*(?:METAD\s+\.\.\.|\.\.\.\s+METAD)\s*$", text, flags=re.MULTILINE
        )
        if len(metad_delimiters) != 2:
            raise ValidationError(f"{relative}: expected one METAD block")
        if not re.search(r"^\s*bias:\s+BIASVALUE\s+ARG=sasa\s*$", text, flags=re.MULTILINE):
            raise ValidationError(f"{relative}: historical BIASVALUE ARG=sasa is missing")
        required = ("ARG=sasa", "PACE=500", "BIASFACTOR=25", "FILE=HILLS", "FILE=COLVAR")
        if not all(token in compact for token in required):
            raise ValidationError(f"{relative}: SASA bias/PRINT parameters differ")


def parse_args() -> argparse.Namespace:
    default_bundle = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle-root",
        type=Path,
        default=default_bundle,
        help="agent bundle root (default: parent of this script)",
    )
    parser.add_argument(
        "--inputs-root",
        type=Path,
        help="input tree to validate (default: BUNDLE_ROOT/inputs; may be RUN_DIR/inputs)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle_root = args.bundle_root.expanduser().resolve()
    inputs_root = (
        args.inputs_root.expanduser().resolve()
        if args.inputs_root is not None
        else bundle_root / "inputs"
    )
    checks: tuple[tuple[str, Callable[[Path], None]], ...] = (
        ("SHA-256", validate_hashes),
        ("atom/index counts", validate_atom_counts),
        ("topology", validate_topology),
        ("distance PLUMED semantics", validate_distance_dat),
        ("SASA PLUMED semantics", validate_sasa_dat),
    )
    failures: list[str] = []
    for name, check in checks:
        try:
            check(inputs_root)
        except (OSError, UnicodeError, ValidationError, ValueError) as exc:
            failures.append(f"{name}: {exc}")
        else:
            print(f"OK: {name}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        print(f"Input validation failed for {inputs_root}", file=sys.stderr)
        return 1
    print(f"OK: validated immutable inputs at {inputs_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

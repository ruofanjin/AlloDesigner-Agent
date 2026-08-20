#!/usr/bin/env python3
"""Validate a Stage6 VS return packet and optionally promote into a MultiAgent run dir."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from statistics import median


REQUIRED_CSV_COLS = {
    "rank",
    "ligand_id",
    "smiles",
    "score",
    "score_type",
    "engine",
    "pocket_id",
    "receptor_frame",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_return(ret: dict, csv_path: Path) -> list[str]:
    errs: list[str] = []
    for k in (
        "schema_version",
        "stage_id",
        "status",
        "product_maturity",
        "engine",
        "protocol_version",
        "inputs_consumed",
        "ranked_candidates_csv",
        "metrics",
        "claims_allowed",
        "claims_forbidden",
    ):
        if k not in ret:
            errs.append(f"missing field: {k}")
    if ret.get("stage_id") != "candidate_ranking":
        errs.append("stage_id must be candidate_ranking")
    if ret.get("engine") not in {"vina", "glide", "karmadock", "dry_run_placeholder"}:
        errs.append(f"unsupported engine: {ret.get('engine')}")
    if not csv_path.is_file():
        errs.append(f"ranked_candidates.csv missing: {csv_path}")
        return errs
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        errs.append("ranked_candidates.csv has no rows")
        return errs
    missing = REQUIRED_CSV_COLS - set(rows[0].keys())
    if missing:
        errs.append(f"csv missing columns: {sorted(missing)}")
    scores = []
    for i, row in enumerate(rows, 1):
        try:
            scores.append(float(row["score"]))
        except Exception:
            errs.append(f"row {i}: bad score")
        if row.get("engine") and row["engine"] != ret.get("engine") and ret.get("engine") != "dry_run_placeholder":
            # allow dry_run; otherwise engine column should match
            if ret.get("engine") in {"vina", "glide"} and row["engine"] != ret["engine"]:
                errs.append(f"row {i}: engine mismatch {row.get('engine')} vs {ret.get('engine')}")
    n = len(rows)
    if ret.get("metrics", {}).get("n_scored") not in (None, n):
        errs.append(f"metrics.n_scored={ret['metrics'].get('n_scored')} != csv rows {n}")
    if scores:
        ret.setdefault("metrics", {})
        # fill if absent
        ret["metrics"].setdefault("score_min", min(scores))
        ret["metrics"].setdefault("score_max", max(scores))
        ret["metrics"].setdefault("score_median", float(median(scores)))
    return errs


def promote(return_dir: Path, run_dir: Path, ret: dict, errs: list[str]) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    dest = (run_dir / "returns" / return_dir.name).resolve()
    src = return_dir.resolve()
    if src != dest:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        # Return already lives under the promote run dir; keep in place.
        dest = src
    stage = {
        "stage_id": "candidate_ranking",
        "status": ret.get("status", "external_completed") if not errs else "failed",
        "product_maturity": ret.get("product_maturity", "partial/seeded"),
        "engine": ret.get("engine"),
        "protocol_version": ret.get("protocol_version"),
        "return_dir": str(dest),
        "validation_errors": errs,
        "metrics": ret.get("metrics"),
        "inputs_consumed": ret.get("inputs_consumed"),
        "claims_allowed": ret.get("claims_allowed"),
        "claims_forbidden": ret.get("claims_forbidden"),
        "doc": "docs/stage6_seeded_job_pack.md",
    }
    out = run_dir / "stage_result.json"
    # merge multi-engine returns if existing
    if out.is_file():
        prev = load_json(out)
        engines = prev.get("engines_returned", {})
        if isinstance(engines, dict):
            engines[ret["engine"]] = {
                "return_dir": str(dest),
                "status": stage["status"],
                "metrics": ret.get("metrics"),
            }
            stage["engines_returned"] = engines
            if prev.get("engines_returned"):
                # keep prior engines
                for k, v in prev["engines_returned"].items():
                    stage["engines_returned"].setdefault(k, v)
    else:
        stage["engines_returned"] = {
            ret["engine"]: {
                "return_dir": str(dest),
                "status": stage["status"],
                "metrics": ret.get("metrics"),
            }
        }
    if stage["engines_returned"] and all(
        v.get("status") in {"demo_completed", "external_completed", "partial_completed"}
        for v in stage["engines_returned"].values()
    ):
        stage["status"] = "demo_completed"
    out.write_text(json.dumps(stage, indent=2) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack-dir", type=Path, required=True)
    ap.add_argument("--return-dir", type=Path, required=True)
    ap.add_argument("--promote-run-dir", type=Path, default=None)
    args = ap.parse_args()
    ret_path = args.return_dir / "return.json"
    csv_path = args.return_dir / "ranked_candidates.csv"
    ret = load_json(ret_path)
    errs = validate_return(ret, csv_path)
    report = {"ok": not errs, "errors": errs, "engine": ret.get("engine"), "return_dir": str(args.return_dir)}
    print(json.dumps(report, indent=2))
    if args.promote_run_dir:
        out = promote(args.return_dir, args.promote_run_dir, ret, errs)
        print(f"wrote {out}")
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())

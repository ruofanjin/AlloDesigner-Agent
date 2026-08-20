from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_stage_contracts(path: Path | None = None) -> dict[str, Any]:
    return load_yaml(path or CONFIG_DIR / "stages.yaml")


def load_reference_path(path: Path | None = None) -> dict[str, Any]:
    return load_yaml(path or CONFIG_DIR / "reference_path.yaml")


def load_tool_registry(path: Path | None = None) -> dict[str, Any]:
    return load_yaml(path or CONFIG_DIR / "tool_registry.yaml")


def ordered_stage_ids(contracts: dict[str, Any]) -> list[str]:
    stages = sorted(contracts["stages"], key=lambda s: s["order"])
    return [s["id"] for s in stages]


def stage_by_id(contracts: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in contracts["stages"]:
        if stage["id"] == stage_id:
            return stage
    raise KeyError(f"Unknown stage_id: {stage_id}")

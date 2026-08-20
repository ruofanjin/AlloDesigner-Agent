"""CLI for contract-constrained autonomous reasoning orchestrator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .models import TaskSpec
from .orchestrator_loop import ReasoningOrchestrator


def load_task(path: Path) -> TaskSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return TaskSpec.model_validate(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="allodesigner-agent",
        description="AlloDesigner contract-constrained reasoning orchestrator",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("reason-run", help="Build ReasoningPlan, critic-gate, execute DAG")
    p_run.add_argument("--task", type=Path, required=True)
    p_run.add_argument("--run-dir", type=Path, default=None)
    p_run.add_argument("--force-missing-stage4", action="store_true")
    p_run.add_argument("--max-replans", type=int, default=2)

    p_plan = sub.add_parser("reason-plan", help="Only emit ReasoningPlan + critic review")
    p_plan.add_argument("--task", type=Path, required=True)
    p_plan.add_argument("--force-missing-stage4", action="store_true")
    p_plan.add_argument("--out", type=Path, default=None)

    args = parser.parse_args(argv)
    if args.cmd == "reason-plan":
        from .reasoning.planner import AutonomousReasoningPlanner
        from .reasoning.critic_gate import ReasoningCritic
        from .contracts import load_stage_contracts

        task = load_task(args.task)
        planner = AutonomousReasoningPlanner()
        plan = planner.build(task, force_missing_stage4=args.force_missing_stage4)
        gate = ReasoningCritic().review_plan(task, plan, load_stage_contracts())
        payload = {
            "critic": gate,
            "reasoning_plan": json.loads(plan.model_dump_json()),
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0 if gate["passed"] else 2

    if args.cmd == "reason-run":
        task = load_task(args.task)
        orch = ReasoningOrchestrator(run_dir=args.run_dir)
        report = orch.run(
            task,
            force_missing_stage4=args.force_missing_stage4,
            max_replans=args.max_replans,
        )
        print(json.dumps({"status": report["status"], "run_dir": report["run_dir"]}, indent=2))
        print("narrative:")
        for line in report.get("reasoning_narrative", []):
            print(" ", line)
        return 0 if report["status"] == "completed" else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

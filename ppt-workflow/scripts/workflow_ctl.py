"""Command-line control plane for the PPT workflow gates."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from workflow_control import (  # noqa: E402
    LAYERS, append_event, artifact_hashes, control_status, event_digest,
    next_layer, read_event_chain, state_digest,
)

TEMPLATE = SCRIPT_DIR.parent / "templates" / "workflow-state.example.json"


@dataclass
class GateResult:
    returncode: int
    passes: int
    failures: int
    summary: str
    output: str


def _task(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.exists() and not resolved.is_dir():
        raise ValueError(f"task path is not a directory: {resolved}")
    return resolved


def _inside(task: Path, relative: str) -> Path:
    candidate = (task / relative).resolve()
    try:
        candidate.relative_to(task)
    except ValueError as exc:
        raise ValueError("path escapes task directory") from exc
    return candidate


def _load(task: Path) -> tuple[dict, Path]:
    state_path = _inside(task, "workflow-state.json")
    with state_path.open(encoding="utf-8") as handle:
        state = json.load(handle)
    if not isinstance(state, dict):
        raise ValueError("workflow-state.json must contain an object")
    return state, state_path


def _write(task: Path, state: dict, state_path: Path) -> None:
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _refresh(task: Path, state: dict) -> None:
    control = state.setdefault("control", {})
    control["artifactHashes"] = artifact_hashes(task, state)
    control["stateSha256"] = state_digest(state)
    _, head = read_event_chain(_inside(task, "workflow-events.jsonl"))
    control["eventHeadSha256"] = head


def _event(task: Path, state: dict, command: str, result: str, from_layer: str, to_layer: str, gate: GateResult | None = None) -> None:
    control = state.setdefault("control", {})
    record = {
        "eventId": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": command,
        "fromLayer": from_layer,
        "toLayer": to_layer,
        "result": result,
        "stateSha256": state_digest(state),
        "artifactHashes": control.get("artifactHashes", {}),
        "gateSummary": {"pass": gate.passes, "fail": gate.failures} if gate else {"pass": 0, "fail": 0},
    }
    head = append_event(_inside(task, "workflow-events.jsonl"), record)
    control["eventHeadSha256"] = head


def run_gate(task_dir: Path, layer: str) -> GateResult:
    command = [sys.executable, str(SCRIPT_DIR / "check_workflow_state.py"), "--task", str(task_dir), "--layer", layer]
    proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = (proc.stdout or "") + (proc.stderr or "")
    passes = sum(1 for line in output.splitlines() if line.startswith("[PASS]"))
    failures = sum(1 for line in output.splitlines() if line.startswith("[FAIL]"))
    summary = next((line for line in output.splitlines() if line.startswith("Summary:")), "")
    return GateResult(proc.returncode, passes, failures, summary, output)


def cmd_init(args: argparse.Namespace) -> int:
    task = _task(args.task)
    state_path = _inside(task, "workflow-state.json")
    log_path = _inside(task, "workflow-events.jsonl")
    if state_path.exists() and not args.force:
        print(f"state already exists: {state_path}", file=sys.stderr)
        return 2
    if args.force and log_path.exists():
        print("--force is only allowed before a control log exists", file=sys.stderr)
        return 2
    task.mkdir(parents=True, exist_ok=True)
    state = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    state.setdefault("task", {})["name"] = args.name
    state["task"]["deliveryFormat"] = args.format
    state["control"] = {"currentLayer": "prep", "status": "active", "toolVersion": "1", "stateSha256": "", "eventHeadSha256": "", "sealedAt": None, "artifactHashes": {}}
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log_path.touch()
    _event(task, state, "init", "pass", "prep", "prep")
    _refresh(task, state)
    _write(task, state, state_path)
    print(f"initialized {task}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    task = _task(args.task)
    try:
        state, _ = _load(task)
        status = control_status(task, state)
        if status != "legacy-unmanaged":
            control = state.get("control", {})
            expected = control.get("artifactHashes", {})
            if "artifactHashes" in control and expected != artifact_hashes(task, state):
                status = "drifted"
        print(status)
        return 0 if status in {"active", "sealed", "legacy-unmanaged"} else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def cmd_verify(args: argparse.Namespace) -> int:
    task = _task(args.task)
    state, state_path = _load(task)
    layer = args.layer
    gate = run_gate(task, layer)
    control = state.setdefault("control", {})
    previous = control.get("currentLayer", "prep")
    control["status"] = "active" if gate.returncode == 0 else "blocked"
    _event(task, state, "verify", "pass" if gate.returncode == 0 else "fail", previous, previous, gate)
    _refresh(task, state)
    _write(task, state, state_path)
    print(gate.output, end="")
    return gate.returncode


def cmd_advance(args: argparse.Namespace) -> int:
    task = _task(args.task)
    state, state_path = _load(task)
    control = state.setdefault("control", {})
    current = control.get("currentLayer", "prep")
    target = args.to
    if control_status(task, state) == "drifted" or ("artifactHashes" in control and control["artifactHashes"] != artifact_hashes(task, state)):
        print("cannot advance a drifted task; verify or reinitialize after restoring files", file=sys.stderr)
        return 1
    if not next_layer(current, target):
        print(f"invalid transition: {current} -> {target}", file=sys.stderr)
        return 2
    gate = run_gate(task, current)
    if gate.returncode != 0:
        control["status"] = "blocked"
        _event(task, state, "advance", "fail", current, current, gate)
        _refresh(task, state)
        _write(task, state, state_path)
        print(gate.output, end="")
        return gate.returncode
    control["currentLayer"] = target
    control["status"] = "active"
    _event(task, state, "advance", "pass", current, target, gate)
    _refresh(task, state)
    _write(task, state, state_path)
    print(f"advanced to {target}")
    return 0


def cmd_seal(args: argparse.Namespace) -> int:
    task = _task(args.task)
    state, state_path = _load(task)
    control = state.setdefault("control", {})
    if control_status(task, state) == "drifted" or ("artifactHashes" in control and control["artifactHashes"] != artifact_hashes(task, state)):
        print("cannot seal a drifted task", file=sys.stderr)
        return 1
    if control.get("currentLayer") != "deliver":
        print("seal requires currentLayer=deliver", file=sys.stderr)
        return 2
    gate = run_gate(task, "deliver")
    if gate.returncode != 0:
        control["status"] = "blocked"
        _event(task, state, "seal", "fail", "deliver", "deliver", gate)
        _refresh(task, state)
        _write(task, state, state_path)
        print(gate.output, end="")
        return gate.returncode
    control["status"] = "sealed"
    control["sealedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _event(task, state, "seal", "pass", "deliver", "deliver", gate)
    _refresh(task, state)
    _write(task, state, state_path)
    print("sealed")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    events, _ = read_event_chain(_inside(_task(args.task), "workflow-events.jsonl"))
    for event in events:
        print(json.dumps(event, ensure_ascii=False, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PPT workflow control plane")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--task", type=Path, required=True); init.add_argument("--name", required=True); init.add_argument("--format", choices=("html", "pptx"), required=True); init.add_argument("--force", action="store_true"); init.set_defaults(func=cmd_init)
    for name, func in (("status", cmd_status), ("log", cmd_log)):
        p = sub.add_parser(name); p.add_argument("--task", type=Path, required=True); p.set_defaults(func=func)
    verify = sub.add_parser("verify"); verify.add_argument("--task", type=Path, required=True); verify.add_argument("--layer", choices=LAYERS + ("all",), required=True); verify.set_defaults(func=cmd_verify)
    advance = sub.add_parser("advance"); advance.add_argument("--task", type=Path, required=True); advance.add_argument("--to", choices=LAYERS[1:], required=True); advance.set_defaults(func=cmd_advance)
    seal = sub.add_parser("seal"); seal.add_argument("--task", type=Path, required=True); seal.set_defaults(func=cmd_seal)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

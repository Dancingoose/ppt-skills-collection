#!/usr/bin/env python3
"""Build and verify the task-local presentation handoff protocol."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PROTOCOL_SCHEMA_VERSION = 1
PROTOCOL_KIND = "ppt-workflow-presentation-protocol"
DEFAULT_ARTIFACT = "presentation-protocol.json"


class ProtocolError(ValueError):
    """Raised when a protocol cannot be safely created or validated."""


def task_artifact_path(task_dir: Path, name: object) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise ProtocolError("protocol artifact path is required")
    try:
        path = (task_dir / name).resolve()
        path.relative_to(task_dir.resolve())
    except (OSError, ValueError) as exc:
        raise ProtocolError("protocol artifact must stay inside the task directory") from exc
    return path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _slide_contract(slide: dict[str, Any]) -> dict[str, Any]:
    evidence = slide.get("layoutEvidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    effect = slide.get("visualEffect")
    effect = effect if isinstance(effect, dict) else {}
    contract = {
        "id": slide.get("id"),
        "layout": slide.get("layout"),
        "contentType": slide.get("contentType"),
        "itemCount": evidence.get("itemCount"),
        "sourceRefs": evidence.get("sourceRefs"),
        "visualEffect": effect,
        "backgroundMode": "dark" if bool(slide.get("dark")) else "light",
    }
    if isinstance(evidence.get("numericValues"), list):
        contract["numericValues"] = evidence["numericValues"]
    for key in ("archetype", "compositionFamily"):
        value = _optional_string(slide.get(key))
        if value is not None:
            contract[key] = value
    return contract


def build_protocol(task_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Derive the protocol from the current execution manifest and HTML."""
    if not isinstance(state, dict):
        raise ProtocolError("workflow state must be an object")
    execution = state.get("execution")
    execution = execution if isinstance(execution, dict) else {}
    html_name = execution.get("html")
    html_path = task_artifact_path(task_dir, html_name)
    if not html_path.is_file():
        raise ProtocolError(f"execution HTML does not exist: {html_name}")
    slides = execution.get("slides")
    if not isinstance(slides, list) or not all(isinstance(slide, dict) for slide in slides):
        raise ProtocolError("execution slides must be a list of objects")

    decision = state.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    phase1 = decision.get("phase1")
    phase1 = phase1 if isinstance(phase1, dict) else {}
    profile = decision.get("designProfile")
    profile = profile if isinstance(profile, dict) else {}
    orchestration = decision.get("designOrchestration")
    orchestration = orchestration if isinstance(orchestration, dict) else {}
    task = state.get("task")
    task = task if isinstance(task, dict) else {}

    return {
        "schemaVersion": PROTOCOL_SCHEMA_VERSION,
        "kind": PROTOCOL_KIND,
        "source": {"html": html_name, "sha256": sha256_file(html_path)},
        "deck": {
            "deliveryFormat": task.get("deliveryFormat"),
            "canvas": phase1.get("canvas"),
            "designRecipeId": _optional_string(orchestration.get("selectedRecipeId")),
            "designProfileId": _optional_string(profile.get("selectedProfileId")),
            "slideIds": [slide.get("id") for slide in slides],
        },
        "slides": [_slide_contract(slide) for slide in slides],
    }


def protocol_errors(task_dir: Path, state: dict[str, Any], protocol: object) -> list[str]:
    """Return fail-closed messages when a payload differs from current inputs."""
    if not isinstance(protocol, dict):
        return ["protocol artifact must contain a JSON object"]
    try:
        expected = build_protocol(task_dir, state)
    except ProtocolError as exc:
        return [str(exc)]

    errors = []
    if protocol.get("schemaVersion") != PROTOCOL_SCHEMA_VERSION:
        errors.append("protocol has an unsupported schema version")
    if protocol.get("kind") != PROTOCOL_KIND:
        errors.append("protocol has an unsupported kind")
    if protocol.get("source") != expected["source"]:
        errors.append("protocol source does not match the current execution HTML")
    if protocol.get("deck") != expected["deck"]:
        errors.append("protocol deck does not match the current workflow decision")
    if protocol.get("slides") != expected["slides"]:
        errors.append("protocol slides do not match the current execution manifest")
    return errors


def declared_protocol_errors(task_dir: Path, state: dict[str, Any]) -> list[str]:
    """Validate the declared state pointer, sidecar bytes, and payload."""
    execution = state.get("execution") if isinstance(state, dict) else None
    execution = execution if isinstance(execution, dict) else {}
    record = execution.get("protocol")
    if not isinstance(record, dict):
        return ["execution protocol is not declared"]
    if record.get("schemaVersion") != PROTOCOL_SCHEMA_VERSION:
        return ["execution protocol pointer has an unsupported schema version"]
    try:
        path = task_artifact_path(task_dir, record.get("artifact"))
    except ProtocolError as exc:
        return [str(exc)]
    if not path.is_file():
        return ["execution protocol artifact does not exist"]
    expected_sha = record.get("sha256")
    if not isinstance(expected_sha, str) or expected_sha.lower() != sha256_file(path):
        return ["execution protocol artifact hash does not match"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["execution protocol artifact is not valid JSON"]
    return protocol_errors(task_dir, state, payload)


def _load_state(task_dir: Path) -> dict[str, Any]:
    path = task_dir / "workflow-state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtocolError("workflow-state.json is not valid JSON") from exc
    if not isinstance(state, dict):
        raise ProtocolError("workflow-state.json must contain an object")
    return state


def sync_protocol(task_dir: Path, artifact_name: str | None = None) -> Path:
    """Write a fresh sidecar and record its immutable file digest in state."""
    task_dir = task_dir.resolve()
    state = _load_state(task_dir)
    execution = state.get("execution")
    if not isinstance(execution, dict):
        raise ProtocolError("workflow state has no execution object")
    record = execution.get("protocol")
    record = record if isinstance(record, dict) else {}
    artifact_name = artifact_name or record.get("artifact") or DEFAULT_ARTIFACT
    artifact_path = task_artifact_path(task_dir, artifact_name)
    state_path = (task_dir / "workflow-state.json").resolve()
    html_path = task_artifact_path(task_dir, execution.get("html"))
    if artifact_path in {state_path, html_path}:
        raise ProtocolError("protocol artifact cannot overwrite workflow state or execution HTML")
    if artifact_path.exists():
        if not artifact_path.is_file():
            raise ProtocolError("protocol artifact path must be a file")
        try:
            existing = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProtocolError("protocol artifact must be absent or an existing presentation protocol") from exc
        if not isinstance(existing, dict) or existing.get("kind") != PROTOCOL_KIND:
            raise ProtocolError("protocol artifact must be absent or an existing presentation protocol")
    protocol = build_protocol(task_dir, state)
    artifact_path.write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    execution["protocol"] = {
        "schemaVersion": PROTOCOL_SCHEMA_VERSION,
        "artifact": artifact_path.relative_to(task_dir).as_posix(),
        "sha256": sha256_file(artifact_path),
    }
    state["execution"] = execution
    (task_dir / "workflow-state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return artifact_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the PPT presentation handoff protocol")
    commands = parser.add_subparsers(dest="command", required=True)
    sync = commands.add_parser("sync", help="write and register the protocol sidecar")
    sync.add_argument("--task", required=True, type=Path)
    sync.add_argument("--artifact")
    verify = commands.add_parser("verify", help="verify the registered protocol sidecar")
    verify.add_argument("--task", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "sync":
            path = sync_protocol(args.task, args.artifact)
            print(f"synchronized {path}")
            return 0
        state = _load_state(args.task.resolve())
        errors = declared_protocol_errors(args.task.resolve(), state)
        if errors:
            for error in errors:
                print(f"[FAIL] {error}")
            return 2
        print("[PASS] execution presentation protocol matches current state and HTML")
        return 0
    except ProtocolError as exc:
        print(f"[FAIL] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

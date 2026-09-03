"""Pure state, artifact, and append-only event-chain helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LAYERS = ("prep", "intent", "design", "decision", "exec", "deliver")


def canonical_json(value: Any, exclude_paths: set[tuple[str, ...]] | None = None) -> bytes:
    excluded = exclude_paths or set()

    def clean(obj: Any, path: tuple[str, ...] = ()) -> Any:
        if path in excluded:
            return None
        if isinstance(obj, dict):
            return {k: clean(v, path + (str(k),)) for k, v in obj.items() if path + (str(k),) not in excluded}
        if isinstance(obj, list):
            return [clean(v, path + (str(i),)) for i, v in enumerate(obj)]
        return obj

    return json.dumps(clean(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def state_digest(state: dict) -> str:
    return sha256_bytes(canonical_json(state, {("control", "stateSha256"), ("control", "eventHeadSha256")}))


def event_digest(event: dict) -> str:
    return sha256_bytes(canonical_json(event, {("eventSha256",)}))


def read_event_chain(path: Path) -> tuple[list[dict], str]:
    if not path.exists():
        return [], ""
    events: list[dict] = []
    previous = ""
    seen: set[str] = set()
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            raise ValueError(f"empty event line {number}")
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid event JSON at line {number}") from exc
        if not isinstance(event, dict) or event.get("schemaVersion") != 1:
            raise ValueError(f"invalid event schema at line {number}")
        digest = event.get("eventSha256")
        if not isinstance(digest, str) or len(digest) != 64 or digest != event_digest(event):
            raise ValueError(f"event hash mismatch at line {number}")
        if digest in seen:
            raise ValueError(f"duplicate event hash at line {number}")
        if event.get("previousEventSha256", "") != previous:
            raise ValueError(f"event chain mismatch at line {number}")
        seen.add(digest)
        events.append(event)
        previous = digest
    return events, previous


def append_event(path: Path, event: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    _, previous = read_event_chain(path)
    record = dict(event)
    record["schemaVersion"] = 1
    record["previousEventSha256"] = previous
    record["eventSha256"] = event_digest(record)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return record["eventSha256"]


def next_layer(current_layer: str, target_layer: str) -> bool:
    try:
        return LAYERS.index(target_layer) == LAYERS.index(current_layer) + 1
    except ValueError:
        return False


def artifact_hashes(task_dir: Path, state: dict) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(task_dir.rglob("*")):
        if not path.is_file() or path.name in {"workflow-events.jsonl", "workflow-state.json"}:
            continue
        rel = path.relative_to(task_dir).as_posix()
        hashes[rel] = sha256_bytes(path.read_bytes())
    return hashes


def control_status(task_dir: Path, state: dict) -> str:
    control = state.get("control")
    log = task_dir / "workflow-events.jsonl"
    if not isinstance(control, dict) or not log.exists():
        return "legacy-unmanaged"
    try:
        _, head = read_event_chain(log)
    except ValueError:
        return "drifted"
    if control.get("stateSha256") != state_digest(state) or control.get("eventHeadSha256", "") != head:
        return "drifted"
    return str(control.get("status", "active"))

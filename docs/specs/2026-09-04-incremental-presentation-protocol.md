# Incremental Presentation Protocol

**Date:** 2026-09-04  
**Status:** Approved for implementation

## Goal

Add a versioned, file-backed handoff contract between approved workflow state,
HTML authoring, conversion, and delivery review. The protocol makes the
per-slide intent that is currently dispersed across `workflow-state.json` and
HTML attributes independently consumable without replacing either system.

## Non-goals

- Do not replace `workflow-state.json`, `check_workflow_state.py`, or the
  HTML-first converter.
- Do not change the root state schema version or invalidate existing tasks.
- Do not introduce a second slide authoring engine or copy third-party code.

## Artifact

The task-local `presentation-protocol.json` uses schema version 1:

```json
{
  "schemaVersion": 1,
  "kind": "ppt-workflow-presentation-protocol",
  "source": {"html": "design.html", "sha256": "<64 hex>"},
  "deck": {
    "deliveryFormat": "pptx",
    "canvas": "ppt169",
    "designRecipeId": "selected-recipe",
    "designProfileId": "selected-profile",
    "slideIds": [1, 2]
  },
  "slides": [{"id": 1, "layout": "B1", "contentType": "cover"}]
}
```

Every slide records its ID, layout, content type, item count, source references,
visual-effect decision, background mode, and, when present, V3 archetype and
composition family. The protocol carries only values already governed by the
existing state contract; it does not create a parallel source of truth.

## Lifecycle

1. The author finishes `design.html` and the execution manifest.
2. `presentation_protocol.py sync --task <task-dir>` writes the sidecar and
   records its path and file SHA-256 in `execution.protocol`.
3. The execution gate compares the sidecar with the current state and HTML.
   A changed source file, manifest, deck identity, or page contract fails
   closed.
4. Delivery consumes the same execution gate before conversion and audit.

New tasks declare the protocol in the example state. Existing tasks without an
`execution.protocol` object remain compatible and are reported by the gate as
legacy protocol mode.

## Safety and Compatibility

- Artifact paths must resolve inside the task directory.
- `sync` overwrites only the declared task-local protocol artifact and updates
  the task's state pointer; it never writes outside the task directory.
- The recorded SHA-256 covers the sidecar bytes. The source hash inside the
  sidecar covers the current HTML bytes.
- The protocol is not accepted as evidence on its own: existing review,
  evidence, HTML-marker, and delivery-audit gates remain authoritative.

## Acceptance Criteria

1. A protocol generated from a task can be verified without parsing prose.
2. HTML, manifest, or protocol mutation after synchronization blocks the
   execution gate.
3. Legacy task states continue to pass their existing gates unchanged.
4. The authoring and delivery instructions document the synchronization step.

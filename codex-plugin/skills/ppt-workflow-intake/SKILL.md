---
name: ppt-workflow-intake
description: Collect and record creator-confirmed intent for a PPT Workflow Studio task. Use immediately after material inventory and before any design review, preview, deck expansion, HTML authoring, or PPTX conversion; it asks the required 12 intent questions in three batches and makes model inference insufficient.
---

# PPT Workflow Intent Intake

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Work inside the task directory containing `workflow-state.json` and `content-inventory.md`. Read `references/material-driven-questioning.md` before asking questions.

1. Do not create `preview.html`, design directions, page plans beyond the material inventory, `design.html`, or a PPTX until this intake is complete. Material may inform recommendations and answer choices, but never replace a creator response.
2. Ask exactly four questions in each batch, then wait for the creator's response before asking the next batch. Do not infer, assume, or silently fill an unanswered item. A creator may choose a recommendation, give a custom answer, or explicitly answer a question already suggested by the material.
3. Ask batch 1: `audience`, `intent`, `coreClaim`, `canvas`. Ask batch 2: `language`, `expectedOutcome`, `useScene`, `deliveryUse`. Ask batch 3: `storyline`, `contentFocus`, `informationDensity`, `referenceStyle`.
4. For material-backed work, derive concise recommendations from `content-inventory.md`; for any recommendation, name it as a recommendation rather than a decision. Keep options grounded in the material and retain a custom-answer path.
5. After all three creator responses, write `decision.intentQuestionnaire` in `workflow-state.json` using the template. It requires `schemaVersion: 1`, `skill: "ppt-workflow-intake"`, `completed: true`, exactly one response for each required ID, its batch number, the asked question, non-empty answer, `source: "creator-confirmed"`, and evidence pointing to the corresponding creator reply. Record one non-empty `creatorConfirmation` for each batch, in batch order.
6. Copy the confirmed values for `audience`, `intent`, `coreClaim`, and `canvas` into `decision.phase1` without changing their meaning; the validator requires exact agreement. Carry the remaining eight answers into the design brief and Phase 2 decisions. Run:

```powershell
python <collection-root>/ppt-workflow/scripts/check_workflow_state.py --layer intent --task <task-dir>
```

Resolve every failure. The `decision`, `exec`, and `deliver` gates repeat this check, so a preview, expansion, or conversion cannot pass without this evidence.

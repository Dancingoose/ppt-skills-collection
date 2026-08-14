# Visual Intent And Deck Quality Design

## Goal

Make a PPT workflow capture visual intent precisely enough to produce distinctly
better decks without forcing every task into one style. The workflow must retain
three usable directions:

- `consulting`: executive, evidence-led, restrained.
- `editorial`: narrative, memorable, and chapter-led.
- `impact`: large-scale, high-contrast, and presentation-led.

The creator chooses the direction through visible sample slides, not an
ambiguous text-only style label. The chosen direction becomes an enforceable
part of the task contract and the final review evaluates the whole deck's
reading rhythm as well as individual-page correctness.

## Scope

This change updates the reusable PPT workflow package only. It does not add
sample reports or generated decks to the repository. It preserves HTML-first
authoring, evidence-backed content, the existing PPTX conversion path, and the
current source/color/output reviews.

## Intent Intake

The canonical intake contains 13 creator-confirmed answers in four batches.
Each interaction has at most four questions.

| Batch | Questions | Purpose |
|---|---|---|
| 1 | audience, decision intent, core claim, canvas | Establish the communication contract. |
| 2 | language, desired audience action, use scene, delivery mode | Establish how the deck will be experienced. |
| 3 | storyline, content focus, information density, design boldness | Establish narrative and composition constraints. |
| 4 | visual direction preview selection | Lock a visible visual direction. |

`referenceStyle` is replaced by the visual direction preview. The new
`expectedOutcome` wording asks for the audience action or decision after the
session; it is not a duplicate of communication intent. `deliveryUse` is
renamed or clarified as delivery mode so the workflow can distinguish a live
talk, an emailed readout, and a hybrid deliverable.

The intent schema advances from version 2 to version 3. Version 1 and version
2 remain readable only when needed for existing task records; new tasks must
use version 3.

## Visual Direction Preview

After the first three batches, the workflow produces a lightweight
`visual-direction-preview.html` containing three independent sample slides.
It uses neutral placeholder content rather than rendering the user's entire
deck three times.

Each candidate must visibly express its direction:

| Direction | Visual contract |
|---|---|
| consulting | conclusion-first title, direct evidence zone, restrained color, analytic chart language, precise annotation |
| editorial | decisive headline, chapter rhythm, controlled image/color-field use, editorial typography, memorable transition pages |
| impact | oversized scale contrast, sparse message, strong compositional move, stage-ready color field, live-talk readability |

The creator selection writes `decision.visualDirection`:

```json
{
  "schemaVersion": 1,
  "selected": "editorial",
  "previewArtifact": "visual-direction-preview.html",
  "candidates": ["consulting", "editorial", "impact"],
  "creatorConfirmation": "Creator selected editorial after reviewing all three samples.",
  "evidence": "creator response reference"
}
```

The decision gate requires all candidates, a valid selected value, a readable
preview artifact, and creator confirmation. No fallback may infer a direction
from the topic, organization, or previous deck.

## Direction-To-Design Mapping

`decision.visualDirection` is copied into the locked passport. The authoring
skill maps it to allowed theme families, typography scale, image usage,
composition patterns, chart treatment, and expected page archetypes. A task
may use exceptions only when they are recorded with a reason.

Every execution slide gains a required `archetype` from:

`hero`, `context`, `evidence`, `data`, `comparison`, `process`, `transition`,
`recommendation`, `action`.

The archetype is distinct from the layout ID. A layout describes geometry; an
archetype describes the reader's job on the page. This makes the workflow able
to assess a deck's narrative rhythm rather than merely count layouts.

## Quality Gates

Existing visual checks remain required. Two file-backed reviews are added after
all HTML slides exist and before conversion.

### Deck Rhythm Review

`deck-rhythm-review.json` records the reading order, every slide's archetype,
chapter boundaries, and the result. It fails when:

- three adjacent slides use the same archetype;
- a 10+ page deck lacks a purposeful hero, data/evidence, and action or
  recommendation moment;
- a long deck has no intentional chapter or transition pause;
- a repeated card-grid page violates the existing 20 percent / three-page
  separation gate.

### Visual Direction Review

`visual-direction-review.json` records the selected direction, reviewed
slides, result, exceptions, and notes. It verifies that the deck's actual
typography, spacing, image treatment, chart language, and composition behavior
match the selected direction. It explicitly rejects a polished cover followed
by generic template-like content pages.

### Independent Quality Review

The existing `execution.independentReview` is expanded with five dimensions:

- hierarchy: the conclusion is evident within three seconds;
- rhythm: the sequence changes reading posture deliberately;
- repetition: layouts and archetypes do not become formulaic;
- evidence: data visuals contain a conclusion and source;
- direction: the pages remain faithful to the selected visual contract.

Each dimension records `pass`, `revised`, or a justified `exception`. Any
unresolved failure blocks the execution gate.

## Files To Change

- `ppt-workflow/SKILL.md`: canonical 13-item, four-batch process and preview
  placement.
- `codex-plugin/skills/ppt-workflow-intake/SKILL.md`: new batch handling and
  visual confirmation artifact.
- `codex-plugin/skills/ppt-workflow-authoring/SKILL.md`: direction mapping and
  per-slide archetype requirement.
- `codex-plugin/skills/ppt-workflow-review/SKILL.md`: deck-rhythm and visual-
  direction reviews.
- `ppt-workflow/templates/workflow-state.example.json`: schema version 3 and
  all new artifacts/fields.
- `ppt-workflow/scripts/check_workflow_state.py`: schema, decision, execution,
  review, and fail-closed validation.
- `ppt-workflow/tests/test_check_workflow_state.py`: focused positive and
  negative regression tests.
- `references/quick-reference-card.md` and
  `references/material-driven-questioning.md`: concise operational guidance.

## Verification

Implementation is complete only when:

1. the new schema accepts exactly 13 answers in `4 + 4 + 4 + 1` batches;
2. a missing or unconfirmed visual preview fails the decision gate;
3. a visual direction that does not match its locked passport fails execution;
4. missing, repeated, or incoherent archetypes fail the new quality gates;
5. a compliant long-form deck passes all prep, intent, decision, execution,
   and delivery checks;
6. all existing workflow and converter tests continue to pass.

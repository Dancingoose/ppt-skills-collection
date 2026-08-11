# Composition Patterns

This catalog turns a layout label into a deliberate composition. It is not a
collection of decorative recipes: every pattern names a visual hierarchy,
content fit, and an export-safe fallback for PPTX.

## Design Boldness

| Level | Profile | Allowed composition behavior |
|---|---|---|
| 1 | conservative | Clear grid, one focal point, restrained type scale and no decorative overlap. |
| 2 | measured | Asymmetric emphasis or one controlled crop, but reading order remains conventional. |
| 3 | expressive | Layered type, decisive scale contrast, one non-rectangular visual move per key slide. |
| 4 | bold | Editorial collision, cropped type, image or chart bleed, and intentional imbalance on chapter pages. |
| 5 | experimental | Immersive composition, controlled overlap, live HTML effects, and a separate PPTX fallback are required. |

Levels 4 and 5 must use at least one composition pattern from the `bold` or
`experimental` group on every chapter opener and on at least 20% of the deck.
They may not be satisfied by adding more lines, small labels, or decorative
shapes to an otherwise generic card grid.

## Patterns

| ID | Group | Composition | Best fit | PPTX fallback |
|---|---|---|---|---|
| P01 | conservative | Framed editorial spread: title, claim, one controlled evidence zone | evidence, teaching | native text and border |
| P02 | conservative | Structured comparison: two unequal columns with an explicit decision axis | comparison | direct grid |
| P03 | measured | Sideways itinerary: oversized day marker crossing a route strip | route, agenda | direct grid and line |
| P04 | measured | Data monument: one figure dominates, evidence supports beneath | numeric claim | native text/chart |
| P05 | measured | Captioned image essay: image establishes context, caption provides proof | visual story | licensed image or no-image substitute |
| P06 | expressive | Split-scale typography: oversized keyword cut by the slide edge, compact evidence block | chapter opener | editable text, no clipping |
| P07 | expressive | Stacked evidence bands: three unequal horizontal zones with progressive hierarchy | process, argument | direct blocks |
| P08 | expressive | Diagonal route field: chronology moves across a tilted visual field, labels stay level | itinerary | snapshot decoration plus text |
| P09 | expressive | Editorial ledger: aligned metadata, marginal notes, and a dominant central assertion | research summary | direct grid |
| P10 | bold | Full-bleed licensed photograph or color field with cropped type and precise caption | cover, place | no-image color-field version |
| P11 | bold | Colliding modules: overlapping but non-obscuring evidence panels with deliberate depth | synthesis | direct blocks; no nested grid |
| P12 | bold | Panorama timeline: large temporal labels, discontinuous route segments, selective detail | journey, evolution | direct grid and line |
| P13 | bold | Data theatre: chart is a stage object, annotation and conclusion occupy the remaining field | data narrative | ECharts static frame plus editable conclusion |
| P14 | experimental | Live terrain: Canvas/WebGL scene behind sparse type, with an explicit live-HTML delivery | spatial story | static snapshot in PPTX |
| P15 | experimental | Responsive story sequence: animated transitions and progressive disclosure | keynote presentation | live HTML plus static PPTX companion |

## Selection Rules

- Record `compositionPattern` for every slide in `execution.slides`.
- Do not repeat the same pattern more than twice consecutively.
- A photo-dependent pattern must have an approved `supplied-image` or
  `web-search` record. Otherwise select its named no-image fallback.
- Use only direct-grid structures for PPTX tables and dense comparisons; do
  not use native HTML tables or nested grid rows.
- Pattern P14 or P15 requires the creator to choose a live HTML companion.

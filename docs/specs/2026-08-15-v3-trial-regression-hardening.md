# V3 Trial Regression Hardening

## Purpose

Harden the reusable PPT workflow against the regressions exposed by the AI
industry trial. This change applies to new V3 tasks only. Existing V1 and V2
task records remain valid.

## Observed Regressions

1. The packaged intake skill still described the pre-V3 question set.
2. Three direction samples could claim different geometry while presenting the
   same left/right composition.
3. A selected warm light direction could still become a mixed dark/light deck
   because background policy was not part of the selected visual contract.
4. A clipped, transformed decoration could survive authoring and only surface
   as a conversion warning.

## Contract Changes

- Extend each V3 candidate visual contract with `backgroundStrategy` and
  `primaryBackgroundMode`. The selected candidate values must exactly match
  the locked passport.
- Require every sample in `visual-direction-preview.html` to declare a
  `data-composition-family`. The three candidates must use three distinct
  families; `asymmetric-columns` is one family and cannot be reused.
- Require V3 execution slides to record a `compositionFamily` and embed the
  same value in the HTML slide container. Reject three consecutive slides
  with the same family, in addition to the existing grid-layout limits.
- Make `uniform` with a light primary mode the default recommendation for a
  management research deck. A dark or rhythmic system is valid only when its
  selected visual contract explicitly requests it.
- Reject high-risk transformed decorations in a clipped slide container at
  preflight. Authoring guidance must prefer non-transformed CSS for PPTX.

## Verification

Add regression tests for stale V3 intake instructions, duplicate candidate
composition families, passport/background-contract drift, repeated execution
composition families, and transformed-decoration preflight failure. Run the
workflow and converter test suites before committing.

---
name: ppt-workflow-intake
description: Collect and record creator-confirmed intent for a PPT Workflow Studio task. V3 uses four batches of 4+4+4+1 questions, with the final question confirming a dynamic visual sample.
---

# PPT Workflow Intent Intake

## V3 样张确认

前三批共 12 项创作者确认后，结合素材和回答生成三张独立视觉样张，而不是要求用户从预设风格标签中选择。每张样张写明适配理由和四维视觉契约；三张任意两张至少在三个维度不同。第 13 项展示这些样张并确认一项。选择“都不符合”时必须收集修改意见，重新生成三项，且不能将问卷标为完成或进入决策层。

## V3 精准约束记录

第 3 批回答后必须把创作者的边界写入 `decision.intentBindings`，不能只保留自然语言问答。至少记录内容必须包含与必须避免的事项、构图必须避免的事项、交付必须支持的条件，并把故事线、内容重点、信息密度、设计大胆程度、期望结果、使用场景和交付用途逐项绑定到对应回答。边界应包含可执行的反例，例如“不得使用无来源的精确预测”，而不是“风格要专业”。

Use the collection root named by `PPT_WORKFLOW_ROOT`; when it is unset, derive it from this installed package. Work inside the task directory containing `workflow-state.json` and `content-inventory.md`. Read `references/material-driven-questioning.md` before asking questions.

1. Do not create `preview.html`, design directions, page plans beyond the material inventory, `design.html`, or a PPTX until this intake is complete. Material may inform recommendations and answer choices, but never replace a creator response.
2. Ask exactly four questions in each batch, then wait for the creator's response before asking the next batch. Do not infer, assume, or silently fill an unanswered item. A creator may choose a recommendation, give a custom answer, or explicitly answer a question already suggested by the material.
3. Ask batch 1: `audience`, `intent`, `coreClaim`, `canvas`. Ask batch 2: `language`, `expectedOutcome`, `useScene`, `deliveryUse`. Ask batch 3: `storyline`, `contentFocus`, `informationDensity`, `designBoldness`. Ask batch 4: `visualSampleConfirmation` only after three data-backed visual samples are shown.
4. For material-backed work, derive concise recommendations from `content-inventory.md`; for any recommendation, name it as a recommendation rather than a decision. Keep options grounded in the material and retain a custom-answer path. For each batch, ask at least one boundary or tradeoff question when the answer changes content, composition, or delivery.
5. After all four creator responses, write `decision.intentQuestionnaire` in `workflow-state.json` using the template. V3 requires `schemaVersion: 3`, `skill: "ppt-workflow-intake"`, `completed: true`, exactly one response for each required ID, its batch number, the asked question, non-empty answer, `source: "creator-confirmed"`, and evidence pointing to the corresponding creator reply. Record one non-empty `creatorConfirmation` for each batch, in batch order.
6. Copy the confirmed values for `audience`, `intent`, `coreClaim`, and `canvas` into `decision.phase1` without changing their meaning; the validator requires exact agreement. Carry the remaining eight answers into the design brief and `decision.intentBindings` for content, composition, and delivery. Run:

```powershell
python <collection-root>/ppt-workflow/scripts/check_workflow_state.py --layer intent --task <task-dir>
```

Resolve every failure. The `decision`, `exec`, and `deliver` gates repeat this check, so a preview, expansion, or conversion cannot pass without this evidence.

"""Capture browser motion and emit a composable native PresentationML timeline.

The converter deliberately renders the final HTML state for editing fidelity.
This module keeps that behavior while exporting the PowerPoint-native subset:
entrances plus motion paths, scale, and rotation behaviors.
"""
from __future__ import annotations

from typing import Any

from lxml import etree
from pptx.oxml.ns import qn


# This runs before adapters.PREPARE_JS freezes CSS animations. It intentionally
# uses the Web Animations API because it exposes both CSS Animations and WAAPI.
CAPTURE_MOTION_JS = r"""
() => {
  const slides = window.__pptxSlides || [];
  const entrances = new Set(['fade', 'wipe-left', 'wipe-right', 'wipe-up',
                             'wipe-down', 'zoom', 'spin']);
  const allowed = new Set([...entrances, 'motion', 'scale', 'rotate']);
  const asMs = (value, fallback) => {
    const n = Number(value);
    return Number.isFinite(n) && n >= 0 ? Math.round(n) : fallback;
  };
  const directionFromTransform = (value) => {
    const text = String(value || '').toLowerCase();
    const nums = text.match(/-?\d+(?:\.\d+)?/g) || [];
    if (/translatey/.test(text)) return Number(nums[0] || 0) < 0 ? 'wipe-up' : 'wipe-down';
    if (/translatex/.test(text)) return Number(nums[0] || 0) < 0 ? 'wipe-left' : 'wipe-right';
    const x = Number(nums[0] || 0), y = Number(nums[1] || 0);
    if (Math.abs(x) >= Math.abs(y) && Math.abs(x) > 0.01) return x < 0 ? 'wipe-left' : 'wipe-right';
    if (Math.abs(y) > 0.01) return y < 0 ? 'wipe-up' : 'wipe-down';
    return null;
  };
  const matrixFor = (transform) => {
    try {
      const matrix = new DOMMatrixReadOnly(transform && transform !== 'none' ? transform : undefined);
      const scaleX = Math.hypot(matrix.a, matrix.b) || 1;
      return {
        x: matrix.e || 0, y: matrix.f || 0,
        scaleX, scaleY: (matrix.a * matrix.d - matrix.b * matrix.c) / scaleX,
        rotation: Math.atan2(matrix.b, matrix.a) * 180 / Math.PI,
      };
    } catch (_) {
      return { x: 0, y: 0, scaleX: 1, scaleY: 1, rotation: 0 };
    }
  };
  const compact = (value) => Math.round(value * 1000000) / 1000000;
  const automaticPlan = (frames, duration, delay, slide) => {
    if (!frames || frames.length < 2) return [];
    const first = frames[0] || {}, last = frames[frames.length - 1] || {};
    const plan = [];
    const fromOpacity = Number(first.opacity), toOpacity = Number(last.opacity);
    if (Number.isFinite(fromOpacity) && Number.isFinite(toOpacity) && fromOpacity < 0.99 && toOpacity >= 0.99) {
      plan.push({ effect: 'fade', duration, delay, trigger: 'click' });
    }
    const from = matrixFor(first.transform), to = matrixFor(last.transform);
    const slideRect = slide.getBoundingClientRect();
    const dx = from.x - to.x, dy = from.y - to.y;
    if (Math.abs(dx) > 0.01 || Math.abs(dy) > 0.01) {
      const trigger = plan.length ? 'with' : 'click';
      const x = compact(dx / Math.max(1, slideRect.width));
      const y = compact(dy / Math.max(1, slideRect.height));
      plan.push({ effect: 'motion', path: `M ${x} ${y} L 0 0 E`, duration, delay: trigger === 'click' ? delay : 0, trigger });
    }
    const sx = from.scaleX / (to.scaleX || 1), sy = from.scaleY / (to.scaleY || 1);
    if (Math.abs(sx - 1) > 0.001 || Math.abs(sy - 1) > 0.001) {
      const trigger = plan.length ? 'with' : 'click';
      plan.push({ effect: 'scale', from: [compact(sx * 100), compact(sy * 100)], to: [100, 100],
                  duration, delay: trigger === 'click' ? delay : 0, trigger });
    }
    const angle = from.rotation - to.rotation;
    if (Math.abs(angle) > 0.01) {
      const trigger = plan.length ? 'with' : 'click';
      plan.push({ effect: 'rotate', from: compact(angle), to: 0,
                  duration, delay: trigger === 'click' ? delay : 0, trigger });
    }
    return plan;
  };
  const explicitPlan = (element, fallbackDuration, fallbackDelay) => {
    const raw = element.getAttribute('data-pptx-motion-plan');
    if (!raw) return null;
    try {
      const entries = JSON.parse(raw);
      if (!Array.isArray(entries) || !entries.length) return null;
      const result = [];
      for (const source of entries) {
        if (!source || typeof source !== 'object') continue;
        const effect = String(source.effect || source.kind || '').trim().toLowerCase();
        if (!allowed.has(effect)) continue;
        const trigger = ['click', 'with', 'after'].includes(String(source.trigger || '').toLowerCase())
          ? String(source.trigger).toLowerCase() : (result.length ? 'after' : 'click');
        result.push({ ...source, effect, trigger,
          duration: Math.max(1, asMs(source.duration, fallbackDuration)),
          delay: asMs(source.delay, trigger === 'click' ? fallbackDelay : 0),
        });
      }
      return result.length ? result : null;
    } catch (_) {
      return null;
    }
  };
  const result = [];
  let nextId = 1;
  for (let slideIndex = 0; slideIndex < slides.length; slideIndex++) {
    const slide = slides[slideIndex];
    const candidateEls = new Set([slide, ...slide.querySelectorAll('[data-pptx-motion], [data-pptx-motion-plan]')]);
    for (const animation of document.getAnimations({subtree: true})) {
      const target = animation.effect && animation.effect.target;
      if (target && (target === slide || slide.contains(target))) candidateEls.add(target);
    }
    for (const element of candidateEls) {
      if (!(element instanceof Element) || !slide.contains(element) && element !== slide) continue;
      const explicit = String(element.getAttribute('data-pptx-motion') || '').trim().toLowerCase();
      const matching = element.getAnimations().filter(a => a.effect && a.effect.target === element);
      const animation = matching.find(a => a.effect && a.effect.getKeyframes && a.effect.getKeyframes().length >= 2);
      const timing = animation && animation.effect.getTiming ? animation.effect.getTiming() : {};
      const frames = animation && animation.effect.getKeyframes ? animation.effect.getKeyframes() : [];
      if (timing && timing.iterations && timing.iterations !== 1) continue;
      const duration = Math.max(1, asMs(timing.duration, asMs(element.dataset.pptxDuration, 600)));
      const delay = asMs(timing.delay, asMs(element.dataset.pptxDelay, 0));
      let plan = explicitPlan(element, duration, delay);
      if (!plan && entrances.has(explicit)) {
        plan = [{ effect: explicit, duration, delay, trigger: 'click' }];
      }
      if (!plan) plan = automaticPlan(frames, duration, delay, slide);
      if (!plan || !plan.length) continue;
      const id = element.getAttribute('data-pptx-motion-id') || `motion-${nextId++}`;
      element.setAttribute('data-pptx-motion-id', id);
      result.push({
        slideIndex,
        id,
        kind: plan[0].effect,
        duration: plan[0].duration,
        delay: plan[0].delay,
        plan,
      });
    }
  }
  window.__pptxMotions = result;
  return result;
}
"""


def capture_motions(page) -> list[dict[str, Any]]:
    """Return source motion snapshots after slide discovery and before freeze."""
    motions = page.evaluate(CAPTURE_MOTION_JS)
    return motions if isinstance(motions, list) else []


def motions_for_slide(motions: list[dict[str, Any]], slide_index: int) -> list[dict[str, Any]]:
    return [motion for motion in motions if motion.get("slideIndex") == slide_index]


def _el(tag: str, **attrs):
    node = etree.Element(qn(f"p:{tag}"))
    for key, value in attrs.items():
        if value is not None:
            node.set(key, str(value))
    return node


def _condition_list(tag: str, delay: int | str):
    conditions = _el(tag)
    conditions.append(_el("cond", delay=delay))
    return conditions


def _target(shape_id: int):
    target = _el("tgtEl")
    sp_target = _el("spTgt", spid=shape_id)
    sp_target.append(_el("bg"))
    target.append(sp_target)
    return target


def _visibility_set(ids, shape_id: int):
    effect = _el("set")
    behavior = _el("cBhvr")
    ctn = _el("cTn", id=next(ids), dur=1, fill="hold")
    ctn.append(_condition_list("stCondLst", 0))
    behavior.append(ctn)
    behavior.append(_target(shape_id))
    attrs = _el("attrNameLst")
    name = _el("attrName")
    name.text = "style.visibility"
    attrs.append(name)
    behavior.append(attrs)
    effect.append(behavior)
    to = _el("to")
    to.append(_el("strVal", val="visible"))
    effect.append(to)
    return effect


def _entrance_effect(ids, shape_id: int, motion: dict[str, Any]):
    """Emit a PowerPoint entrance effect using documented PresentationML."""
    kind = motion["kind"]
    if kind == "spin":
        effect = _el("animRot", by=21600000)
        behavior = _el("cBhvr")
        behavior.append(_el("cTn", id=next(ids), dur=motion["duration"], fill="hold", nodeType="withEffect"))
        behavior.append(_target(shape_id))
        names = _el("attrNameLst")
        name = _el("attrName")
        name.text = "r"
        names.append(name)
        behavior.append(names)
        effect.append(behavior)
        return effect, "emph", "8"

    filters = {
        "fade": "fade",
        "wipe-left": "wipe(left)",
        "wipe-right": "wipe(right)",
        "wipe-up": "wipe(up)",
        "wipe-down": "wipe(down)",
        "zoom": "circle(in)",
    }
    effect = _el("animEffect", transition="in", filter=filters[kind])
    behavior = _el("cBhvr")
    behavior.append(_el("cTn", id=next(ids), dur=motion["duration"]))
    behavior.append(_target(shape_id))
    effect.append(behavior)
    return effect, "entr", "10" if kind == "fade" else "0"


def _duration(value: Any, fallback: int = 600) -> int:
    try:
        return max(1, int(round(float(value))))
    except (TypeError, ValueError):
        return fallback


def _delay(value: Any, fallback: int = 0) -> int:
    try:
        return max(0, int(round(float(value))))
    except (TypeError, ValueError):
        return fallback


def _number(value: Any, fallback: float = 0.0) -> float:
    try:
        number = float(value)
        return number if number == number and abs(number) != float("inf") else fallback
    except (TypeError, ValueError):
        return fallback


def _point(value: Any, fallback: tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return _number(value[0], fallback[0]), _number(value[1], fallback[1])
    return fallback


def _motion_effect(ids, shape_id: int, action: dict[str, Any]):
    path = str(action.get("path", "M 0 0 L 0 0 E"))
    effect = _el("animMotion", origin="layout", path=path, pathEditMode="relative")
    behavior = _el("cBhvr", **{"from": "", "to": ""})
    behavior.append(_el("cTn", id=next(ids), dur=_duration(action.get("duration")), fill="hold"))
    behavior.append(_target(shape_id))
    attrs = _el("attrNameLst")
    for attr in ("ppt_x", "ppt_y"):
        name = _el("attrName")
        name.text = attr
        attrs.append(name)
    behavior.append(attrs)
    effect.append(behavior)
    return effect


def _scale_effect(ids, shape_id: int, action: dict[str, Any]):
    from_x, from_y = _point(action.get("from"), (100.0, 100.0))
    to_x, to_y = _point(action.get("to"), (100.0, 100.0))
    # PresentationML uses 1/1000 percent: 80% is 800, not 80000.
    effect = _el("animScale")
    behavior = _el("cBhvr")
    behavior.append(_el("cTn", id=next(ids), dur=_duration(action.get("duration")), fill="hold"))
    behavior.append(_target(shape_id))
    effect.append(behavior)
    start = _el("from", x=round(from_x * 10), y=round(from_y * 10))
    end = _el("to", x=round(to_x * 10), y=round(to_y * 10))
    effect.extend((start, end))
    return effect


def _rotation_effect(ids, shape_id: int, action: dict[str, Any]):
    attrs = {}
    if "from" in action:
        attrs["from"] = round(_number(action.get("from"), 0.0) * 60000)
    if "to" in action:
        attrs["to"] = round(_number(action.get("to"), 0.0) * 60000)
    if "by" in action:
        attrs["by"] = round(_number(action.get("by"), 360.0) * 60000)
    effect = _el("animRot", **attrs)
    behavior = _el("cBhvr")
    behavior.append(_el("cTn", id=next(ids), dur=_duration(action.get("duration")), fill="hold"))
    behavior.append(_target(shape_id))
    names = _el("attrNameLst")
    name = _el("attrName")
    name.text = "r"
    names.append(name)
    behavior.append(names)
    effect.append(behavior)
    return effect


def _action_effect(ids, shape_id: int, action: dict[str, Any]):
    kind = str(action.get("effect", action.get("kind", ""))).lower()
    if kind == "motion":
        return _motion_effect(ids, shape_id, action), "entr", "0", False
    if kind == "scale":
        return _scale_effect(ids, shape_id, action), "entr", "0", False
    if kind in {"rotate", "spin"}:
        # A supplied `by` is the familiar spin shorthand; from/to gives a
        # reversible transform that returns to the static final HTML state.
        return _rotation_effect(ids, shape_id, action), "emph", "8", False
    child, preset_class, preset_id = _entrance_effect(ids, shape_id, {
        **action, "kind": kind, "duration": _duration(action.get("duration")),
    })
    return child, preset_class, preset_id, True


def _effect_par(ids, shape_id: int, action: dict[str, Any]):
    child, preset_class, preset_id, entrance = _action_effect(ids, shape_id, action)
    trigger = str(action.get("trigger", "click")).lower()
    node_type = {"with": "withEffect", "after": "afterEffect"}.get(trigger, "clickEffect")
    par = _el("par")
    ctn = _el(
        "cTn", id=next(ids), fill="hold",
        nodeType="clickEffect", grpId=0, presetID=preset_id,
        presetClass=preset_class, presetSubtype="0",
    )
    ctn.set("nodeType", node_type)
    ctn.append(_condition_list("stCondLst", _delay(action.get("delay"), 0)))
    children = _el("childTnLst")
    if entrance:
        children.append(_visibility_set(ids, shape_id))
    children.append(child)
    ctn.append(children)
    par.append(ctn)
    return par


def _normalize_plan(motion: dict[str, Any]) -> list[dict[str, Any]]:
    plan = motion.get("plan")
    if not isinstance(plan, list) or not plan:
        plan = [{"effect": motion.get("kind"), "duration": motion.get("duration", 600),
                 "delay": motion.get("delay", 0), "trigger": "click"}]
    normalized = []
    for index, action in enumerate(plan):
        if not isinstance(action, dict):
            continue
        effect = str(action.get("effect", action.get("kind", ""))).lower()
        if effect not in {"fade", "wipe-left", "wipe-right", "wipe-up", "wipe-down", "zoom",
                          "spin", "motion", "scale", "rotate"}:
            continue
        item = dict(action)
        item["effect"] = effect
        if effect == "spin" and not any(key in item for key in ("by", "from", "to")):
            item["by"] = 360
        item["duration"] = _duration(item.get("duration"), _duration(motion.get("duration")))
        trigger = str(item.get("trigger", "click" if index == 0 else "after")).lower()
        item["trigger"] = trigger if trigger in {"click", "with", "after"} else ("click" if index == 0 else "after")
        item["delay"] = _delay(item.get("delay"), _delay(motion.get("delay"), 0))
        normalized.append(item)
    return normalized


def _timing_tree(bound: list[tuple[dict[str, Any], int]]):
    """Build the minimum main-sequence hierarchy emitted by PowerPoint."""
    ids = iter(range(1, 1000000))
    timing = _el("timing")
    tn_list = _el("tnLst")
    timing.append(tn_list)
    root_par = _el("par")
    tn_list.append(root_par)
    root = _el("cTn", id=next(ids), dur="indefinite", restart="never", nodeType="tmRoot")
    root_par.append(root)
    root_children = _el("childTnLst")
    root.append(root_children)
    sequence = _el("seq", concurrent=1, nextAc="seek")
    root_children.append(sequence)
    main = _el("cTn", id=next(ids), dur="indefinite", nodeType="mainSeq")
    sequence.append(main)
    main_children = _el("childTnLst")
    main.append(main_children)

    click_par = _el("par")
    main_children.append(click_par)
    click = _el("cTn", id=next(ids), fill="hold")
    click.append(_condition_list("stCondLst", "indefinite"))
    click_par.append(click)
    click_children = _el("childTnLst")
    click.append(click_children)
    group_par = _el("par")
    click_children.append(group_par)
    group = _el("cTn", id=next(ids), fill="hold")
    group.append(_condition_list("stCondLst", 0))
    group_par.append(group)
    group_children = _el("childTnLst")
    group.append(group_children)

    previous = _el("prevCondLst")
    prev_cond = _el("cond", evt="onPrev", delay=0)
    prev_target = _el("tgtEl")
    prev_target.append(_el("sldTgt"))
    prev_cond.append(prev_target)
    previous.append(prev_cond)
    sequence.append(previous)
    following = _el("nextCondLst")
    next_cond = _el("cond", evt="onNext", delay=0)
    next_target = _el("tgtEl")
    next_target.append(_el("sldTgt"))
    next_cond.append(next_target)
    following.append(next_cond)
    sequence.append(following)

    build_list = _el("bldLst")
    timing.append(build_list)
    for motion, shape_id in bound:
        for action in _normalize_plan(motion):
            group_children.append(_effect_par(ids, shape_id, action))
        build_list.append(_el("bldP", spid=shape_id, grpId=0,
                              build="allAtOnce", animBg=1))
    return timing


def apply_native_animations(slide, motions: list[dict[str, Any]], target_map: dict[str, Any]) -> dict[str, Any]:
    """Attach a native timeline and return emitted/skipped identifiers."""
    bound = []
    skipped = []
    for motion in motions or []:
        shape = target_map.get(motion.get("id"))
        if shape is None:
            skipped.append(motion.get("id"))
            continue
        bound.append((motion, shape.shape_id))
    if not bound:
        return {"emitted": [], "skipped": skipped}

    root = slide._element
    existing = root.find(qn("p:timing"))
    if existing is not None:
        root.remove(existing)
    timing = _timing_tree(bound)
    insert_at = len(root)
    for idx, child in enumerate(root):
        if child.tag in {qn("p:transition"), qn("p:extLst")}:
            insert_at = idx
            break
    root.insert(insert_at, timing)
    return {"emitted": [motion["id"] for motion, _ in bound], "skipped": skipped}

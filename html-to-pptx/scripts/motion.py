"""Capture supported browser motion and emit native PresentationML timing.

The converter deliberately renders the final HTML state for editing fidelity.
This module preserves that behavior and adds a slideshow-only entrance timeline
for the subset of CSS/WAAPI motion PowerPoint can express reliably.
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
  const allowed = new Set(['fade', 'wipe-left', 'wipe-right', 'wipe-up',
                           'wipe-down', 'zoom', 'spin']);
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
  const inferKind = (frames) => {
    if (!frames || frames.length < 2) return null;
    const first = frames[0] || {}, last = frames[frames.length - 1] || {};
    const fromOpacity = Number(first.opacity), toOpacity = Number(last.opacity);
    if (Number.isFinite(fromOpacity) && Number.isFinite(toOpacity) && fromOpacity < 0.99 && toOpacity >= 0.99) return 'fade';
    const transform = String(first.transform || '');
    if (/translate/i.test(transform)) return directionFromTransform(transform);
    if (/scale/i.test(transform)) return 'zoom';
    if (/rotate/i.test(transform)) return 'spin';
    return null;
  };
  const result = [];
  let nextId = 1;
  for (let slideIndex = 0; slideIndex < slides.length; slideIndex++) {
    const slide = slides[slideIndex];
    const candidateEls = new Set([slide, ...slide.querySelectorAll('[data-pptx-motion]')]);
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
      const kind = explicit || inferKind(frames);
      if (!allowed.has(kind)) continue;
      if (timing && timing.iterations && timing.iterations !== 1) continue;
      const id = element.getAttribute('data-pptx-motion-id') || `motion-${nextId++}`;
      element.setAttribute('data-pptx-motion-id', id);
      result.push({
        slideIndex,
        id,
        kind,
        duration: Math.max(1, asMs(timing.duration, asMs(element.dataset.pptxDuration, 600))),
        delay: asMs(timing.delay, asMs(element.dataset.pptxDelay, 0)),
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


def _effect_par(ids, shape_id: int, motion: dict[str, Any]):
    child, preset_class, preset_id = _entrance_effect(ids, shape_id, motion)
    par = _el("par")
    ctn = _el(
        "cTn", id=next(ids), fill="hold",
        nodeType="clickEffect", grpId=0, presetID=preset_id,
        presetClass=preset_class, presetSubtype="0",
    )
    ctn.append(_condition_list("stCondLst", motion["delay"]))
    children = _el("childTnLst")
    children.append(_visibility_set(ids, shape_id))
    children.append(child)
    ctn.append(children)
    par.append(ctn)
    return par


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
        group_children.append(_effect_par(ids, shape_id, motion))
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

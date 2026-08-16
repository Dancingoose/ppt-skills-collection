"""Audit PowerPoint-native motion without driving the visible desktop UI.

The OOXML checks catch exporter mistakes that the Animation Pane alone hides.
On Windows, PowerPoint COM adds a recognition check. Neither check claims that
someone watched the slideshow; that observation is recorded separately by the
workflow manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def _slide_parts(archive: ZipFile) -> list[str]:
    names = [name for name in archive.namelist()
             if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
    return sorted(names, key=lambda name: int(name.rsplit("slide", 1)[1].split(".", 1)[0]))


def _nonempty_text_shape_ids(root) -> set[str]:
    ids: set[str] = set()
    for shape in root.xpath(".//p:sp", namespaces=NS):
        shape_id = shape.xpath("string(./p:nvSpPr/p:cNvPr/@id)", namespaces=NS)
        text = "".join(shape.xpath(".//a:t/text()", namespaces=NS)).strip()
        if shape_id and text:
            ids.add(shape_id)
    return ids


def _ooxml_slide_audit(root, index: int) -> dict:
    text_ids = _nonempty_text_shape_ids(root)
    builds = root.xpath(".//p:bldP", namespaces=NS)
    text_builds = [build for build in builds if build.get("spid") in text_ids]
    text_background_builds = [build for build in text_builds if build.get("animBg") == "1"]
    click_groups = root.xpath(
        ".//p:cTn[p:stCondLst/p:cond[@delay='indefinite']]", namespaces=NS
    )
    return {
        "index": index,
        "clickGroups": len(click_groups),
        "withEffects": int(root.xpath("count(.//p:cTn[@nodeType='withEffect'])", namespaces=NS)),
        "backgroundTargetCount": int(root.xpath("count(.//p:spTgt/p:bg)", namespaces=NS)),
        "textBuilds": len(text_builds),
        "textBackgroundOnlyBuilds": len(text_background_builds),
    }


def _powerpoint_com_audit(pptx_path: Path) -> dict:
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return {"status": "unavailable", "reason": "pywin32 is not installed", "slides": []}

    app = None
    owns_app = False
    presentation = None
    initialized = False
    try:
        pythoncom.CoInitialize()
        initialized = True
        try:
            app = win32com.client.GetActiveObject("PowerPoint.Application")
        except Exception:
            app = win32com.client.Dispatch("PowerPoint.Application")
            owns_app = True
        presentation = app.Presentations.Open(str(pptx_path.resolve()), True, False, False)
        slides = []
        for index, slide in enumerate(presentation.Slides, start=1):
            sequence = slide.TimeLine.MainSequence
            count = sequence.Count
            text_effects = 0
            triggers = {"click": 0, "with": 0, "after": 0, "other": 0}
            for effect_index in range(1, count + 1):
                effect = sequence.Item(effect_index)
                try:
                    if effect.Shape.TextFrame.HasText:
                        text_effects += 1
                except Exception:
                    pass
                trigger = getattr(effect.Timing, "TriggerType", None)
                key = {1: "click", 2: "with", 3: "after"}.get(trigger, "other")
                triggers[key] += 1
            slides.append({"index": index, "effects": count, "textEffects": text_effects,
                           "triggers": triggers})
        return {"status": "pass", "slides": slides}
    except Exception as exc:
        return {"status": "failed", "reason": str(exc), "slides": []}
    finally:
        if presentation is not None:
            try:
                presentation.Close()
            except Exception:
                pass
        if app is not None and owns_app:
            try:
                app.Quit()
            except Exception:
                pass
        if initialized:
            pythoncom.CoUninitialize()


def audit_motion(pptx_path: Path, include_powerpoint_com: bool = True) -> dict:
    """Return a serializable native-motion audit for *pptx_path*."""
    pptx_path = Path(pptx_path).resolve()
    with ZipFile(pptx_path) as archive:
        slides = [_ooxml_slide_audit(etree.fromstring(archive.read(name)), index)
                  for index, name in enumerate(_slide_parts(archive), start=1)]
    failures = [slide for slide in slides
                if slide["backgroundTargetCount"] or slide["textBackgroundOnlyBuilds"]]
    com = _powerpoint_com_audit(pptx_path) if include_powerpoint_com else {
        "status": "unavailable", "reason": "PowerPoint COM check was not requested", "slides": []
    }
    result = "pass" if not failures and com["status"] != "failed" else "fail"
    return {
        "schemaVersion": 1,
        "kind": "native-motion-audit",
        "result": result,
        "pptx": pptx_path.name,
        "pptxSha256": hashlib.sha256(pptx_path.read_bytes()).hexdigest(),
        "slides": slides,
        "powerPointCom": com,
        "slideshowPlayback": {"observed": False, "observer": "", "evidence": ""},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit native PowerPoint motion in a PPTX")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-powerpoint-com", action="store_true")
    args = parser.parse_args()
    result = audit_motion(args.pptx, include_powerpoint_com=not args.no_powerpoint_com)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[motion-audit] {result['result']} -> {args.out}")
    if result["result"] != "pass":
        sys.exit(2)


if __name__ == "__main__":
    main()

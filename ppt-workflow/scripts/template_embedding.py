#!/usr/bin/env python3
"""Create append-only template copies and audit their protected PPTX parts."""
import argparse
import hashlib
import json
import re
import zipfile
from xml.dom import Node
from pathlib import Path

from defusedxml import minidom


PRESENTATION = "ppt/presentation.xml"
PRESENTATION_RELS = "ppt/_rels/presentation.xml.rels"
CONTENT_TYPES = "[Content_Types].xml"
STRUCTURAL_PARTS = {PRESENTATION, PRESENTATION_RELS, CONTENT_TYPES}
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
SLIDE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
SLIDE_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_parts(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path) as archive:
            return {info.filename: archive.read(info.filename) for info in archive.infolist()}
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"Cannot read PPTX package {path}: {exc}") from exc


def slide_parts(parts: dict[str, bytes]) -> list[tuple[int, str]]:
    found = []
    for part in parts:
        match = SLIDE_RE.match(part)
        if match:
            found.append((int(match.group(1)), part))
    return sorted(found)


def slide_rels_part(slide_part: str) -> str:
    folder, filename = slide_part.rsplit("/", 1)
    return f"{folder}/_rels/{filename}.rels"


def parse_xml(data: bytes, part: str):
    try:
        return minidom.parseString(data)
    except Exception as exc:
        raise ValueError(f"Cannot parse OOXML part {part}: {exc}") from exc


def xml_bytes(document) -> bytes:
    return document.toxml(encoding="UTF-8")


def children(element, namespace: str, local_name: str):
    return [
        node for node in element.childNodes
        if node.nodeType == node.ELEMENT_NODE
        and node.namespaceURI == namespace
        and node.localName == local_name
    ]


def get_single(document, namespace: str, local_name: str, part: str):
    nodes = document.getElementsByTagNameNS(namespace, local_name)
    if len(nodes) != 1:
        raise ValueError(f"Expected one {local_name} element in {part}, found {len(nodes)}")
    return nodes[0]


def profile_template(template: Path) -> dict:
    parts = read_parts(template)
    missing = [part for part in (PRESENTATION, PRESENTATION_RELS, CONTENT_TYPES) if part not in parts]
    if missing:
        raise ValueError(f"PPTX package is missing required parts: {', '.join(missing)}")
    slides = slide_parts(parts)
    if not slides:
        raise ValueError("PPTX package contains no slides to use as an embedding base.")
    return {
        "schemaVersion": 1,
        "mode": "append-only-template-embedding",
        "template": {
            "path": str(template.resolve()),
            "sha256": sha256(template.read_bytes()),
            "slideCount": len(slides),
        },
        "approvedBaseSlides": [],
        "safeZones": [],
        "protectedParts": [
            {"part": name, "sha256": sha256(parts[name])}
            for name in sorted(parts)
            if name not in STRUCTURAL_PARTS
        ],
        "structuralParts": [
            {"part": name, "sha256": sha256(parts[name])}
            for name in sorted(STRUCTURAL_PARTS)
        ],
        "rules": {
            "preserveExistingSlides": True,
            "preserveMastersLayoutsThemesAndMedia": True,
            "allowOnlyAppendedSlides": True,
            "requireVisualReview": True,
        },
    }


def next_relationship_id(document) -> str:
    values = []
    for node in document.getElementsByTagNameNS(REL_NS, "Relationship"):
        match = re.fullmatch(r"rId(\d+)", node.getAttribute("Id"))
        if match:
            values.append(int(match.group(1)))
    return f"rId{max(values, default=0) + 1}"


def append_slide_registration(parts: dict[str, bytes], slide_number: int):
    presentation = parse_xml(parts[PRESENTATION], PRESENTATION)
    slide_ids = get_single(presentation, P_NS, "sldIdLst", PRESENTATION)
    existing_ids = [
        int(node.getAttribute("id"))
        for node in children(slide_ids, P_NS, "sldId")
        if node.getAttribute("id").isdigit()
    ]

    relationships = parse_xml(parts[PRESENTATION_RELS], PRESENTATION_RELS)
    relationship_id = next_relationship_id(relationships)
    slide_id = max(existing_ids, default=255) + 1
    slide_node = presentation.createElementNS(P_NS, "p:sldId")
    slide_node.setAttribute("id", str(slide_id))
    slide_node.setAttributeNS(R_NS, "r:id", relationship_id)
    slide_ids.appendChild(slide_node)

    rels_root = relationships.documentElement
    relationship = relationships.createElementNS(REL_NS, "Relationship")
    relationship.setAttribute("Id", relationship_id)
    relationship.setAttribute("Type", SLIDE_REL_TYPE)
    relationship.setAttribute("Target", f"slides/slide{slide_number}.xml")
    rels_root.appendChild(relationship)

    content_types = parse_xml(parts[CONTENT_TYPES], CONTENT_TYPES)
    overrides = content_types.getElementsByTagNameNS(CT_NS, "Override")
    source_type = next(
        (node.getAttribute("ContentType") for node in overrides
         if node.getAttribute("PartName").startswith("/ppt/slides/slide")),
        SLIDE_CONTENT_TYPE,
    )
    override = content_types.createElementNS(CT_NS, "Override")
    override.setAttribute("PartName", f"/ppt/slides/slide{slide_number}.xml")
    override.setAttribute("ContentType", source_type)
    content_types.documentElement.appendChild(override)

    parts[PRESENTATION] = xml_bytes(presentation)
    parts[PRESENTATION_RELS] = xml_bytes(relationships)
    parts[CONTENT_TYPES] = xml_bytes(content_types)


def clone_background_slide(template: Path, output: Path, source_slide: int, count: int) -> list[dict]:
    if count < 1:
        raise ValueError("Clone count must be at least one.")
    parts = read_parts(template)
    source_part = f"ppt/slides/slide{source_slide}.xml"
    if source_part not in parts:
        raise ValueError(f"Template does not contain source slide {source_slide}.")
    existing = [number for number, _ in slide_parts(parts)]
    next_number = max(existing) + 1
    source_rels = slide_rels_part(source_part)
    created = []
    for _ in range(count):
        target_part = f"ppt/slides/slide{next_number}.xml"
        parts[target_part] = parts[source_part]
        if source_rels in parts:
            parts[slide_rels_part(target_part)] = parts[source_rels]
        append_slide_registration(parts, next_number)
        created.append({"sourceSlide": source_slide, "newSlide": next_number, "part": target_part})
        next_number += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)
    return created


def presentation_relationships(parts: dict[str, bytes]) -> dict[str, tuple[str, str]]:
    document = parse_xml(parts[PRESENTATION_RELS], PRESENTATION_RELS)
    return {
        node.getAttribute("Id"): (node.getAttribute("Type"), node.getAttribute("Target"))
        for node in document.getElementsByTagNameNS(REL_NS, "Relationship")
    }


def presentation_slide_ids(parts: dict[str, bytes]) -> list[tuple[str, str]]:
    document = parse_xml(parts[PRESENTATION], PRESENTATION)
    slide_ids = get_single(document, P_NS, "sldIdLst", PRESENTATION)
    return [
        (node.getAttribute("id"), node.getAttributeNS(R_NS, "id"))
        for node in children(slide_ids, P_NS, "sldId")
    ]


def content_type_overrides(parts: dict[str, bytes]) -> dict[str, str]:
    document = parse_xml(parts[CONTENT_TYPES], CONTENT_TYPES)
    return {
        node.getAttribute("PartName"): node.getAttribute("ContentType")
        for node in document.getElementsByTagNameNS(CT_NS, "Override")
    }


def xml_signature(node):
    if node.nodeType == Node.TEXT_NODE:
        return ("text", node.data) if node.data.strip() else None
    if node.nodeType != Node.ELEMENT_NODE:
        return None
    attributes = tuple(sorted(
        (node.attributes.item(index).namespaceURI or "", node.attributes.item(index).localName or "",
         node.attributes.item(index).value)
        for index in range(node.attributes.length)
    ))
    children_signature = tuple(
        signature for child in node.childNodes
        if (signature := xml_signature(child)) is not None
    )
    return ("element", node.namespaceURI, node.localName, attributes, children_signature)


def remove_nodes(nodes):
    for node in nodes:
        node.parentNode.removeChild(node)


def has_only_appended_structural_changes(original: dict[str, bytes], candidate: dict[str, bytes], new_slides: list[str]) -> list[str]:
    errors = []
    original_presentation = parse_xml(original[PRESENTATION], PRESENTATION)
    candidate_presentation = parse_xml(candidate[PRESENTATION], PRESENTATION)
    original_slide_list = get_single(original_presentation, P_NS, "sldIdLst", PRESENTATION)
    candidate_slide_list = get_single(candidate_presentation, P_NS, "sldIdLst", PRESENTATION)
    original_ids = children(original_slide_list, P_NS, "sldId")
    candidate_ids = children(candidate_slide_list, P_NS, "sldId")
    remove_nodes(candidate_ids[len(original_ids):])
    if xml_signature(original_presentation.documentElement) != xml_signature(candidate_presentation.documentElement):
        errors.append("Presentation structure changed outside appended slide registrations.")

    original_rels = parse_xml(original[PRESENTATION_RELS], PRESENTATION_RELS)
    candidate_rels = parse_xml(candidate[PRESENTATION_RELS], PRESENTATION_RELS)
    original_rel_ids = {
        node.getAttribute("Id")
        for node in original_rels.getElementsByTagNameNS(REL_NS, "Relationship")
    }
    allowed_targets = {part.removeprefix("ppt/") for part in new_slides}
    extra_relationships = [
        node for node in candidate_rels.getElementsByTagNameNS(REL_NS, "Relationship")
        if node.getAttribute("Id") not in original_rel_ids
        and node.getAttribute("Type") == SLIDE_REL_TYPE
        and node.getAttribute("Target") in allowed_targets
    ]
    remove_nodes(extra_relationships)
    if xml_signature(original_rels.documentElement) != xml_signature(candidate_rels.documentElement):
        errors.append("Presentation relationships changed outside appended slides.")

    original_content_types = parse_xml(original[CONTENT_TYPES], CONTENT_TYPES)
    candidate_content_types = parse_xml(candidate[CONTENT_TYPES], CONTENT_TYPES)
    allowed_part_names = {f"/{part}" for part in new_slides}
    extra_overrides = [
        node for node in candidate_content_types.getElementsByTagNameNS(CT_NS, "Override")
        if node.getAttribute("PartName") in allowed_part_names
    ]
    remove_nodes(extra_overrides)
    if xml_signature(original_content_types.documentElement) != xml_signature(candidate_content_types.documentElement):
        errors.append("Content types changed outside appended slides.")
    return errors


def verify_template_integrity(template: Path, output: Path) -> dict:
    original = read_parts(template)
    candidate = read_parts(output)
    missing = sorted(set(original) - set(candidate))
    changed = sorted(
        part for part, data in original.items()
        if part not in STRUCTURAL_PARTS and candidate.get(part) != data
    )
    original_slide_ids = presentation_slide_ids(original)
    output_slide_ids = presentation_slide_ids(candidate)
    original_relationships = presentation_relationships(original)
    output_relationships = presentation_relationships(candidate)
    original_overrides = content_type_overrides(original)
    output_overrides = content_type_overrides(candidate)
    structural_errors = []
    if output_slide_ids[:len(original_slide_ids)] != original_slide_ids:
        structural_errors.append("Existing presentation slide registrations changed or were reordered.")
    for relationship_id, relationship in original_relationships.items():
        if output_relationships.get(relationship_id) != relationship:
            structural_errors.append(f"Existing presentation relationship changed: {relationship_id}")
    for part, content_type in original_overrides.items():
        if output_overrides.get(part) != content_type:
            structural_errors.append(f"Existing content-type override changed: {part}")
    new_slides = [part for _, part in slide_parts(candidate) if part not in original]
    structural_errors.extend(has_only_appended_structural_changes(original, candidate, new_slides))
    result = "pass" if not (missing or changed or structural_errors) else "fail"
    return {
        "schemaVersion": 1,
        "kind": "template-integrity-audit",
        "result": result,
        "template": str(template.resolve()),
        "templateSha256": sha256(template.read_bytes()),
        "output": str(output.resolve()),
        "outputSha256": sha256(output.read_bytes()),
        "protectedPartsChecked": len(original) - len(STRUCTURAL_PARTS),
        "missingParts": missing,
        "changedProtectedParts": changed,
        "structuralErrors": structural_errors,
        "newSlideParts": new_slides,
    }


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="Create a template-preservation plan.")
    inspect_parser.add_argument("--template", required=True, type=Path)
    inspect_parser.add_argument("--out", required=True, type=Path)
    clone_parser = subparsers.add_parser("clone", help="Clone a template background slide into an append-only copy.")
    clone_parser.add_argument("--template", required=True, type=Path)
    clone_parser.add_argument("--out", required=True, type=Path)
    clone_parser.add_argument("--source-slide", required=True, type=int)
    clone_parser.add_argument("--count", default=1, type=int)
    clone_parser.add_argument("--manifest", type=Path, help="Optional file that records the cloned slide mapping.")
    verify_parser = subparsers.add_parser("verify", help="Verify that protected template parts are unchanged.")
    verify_parser.add_argument("--template", required=True, type=Path)
    verify_parser.add_argument("--output", required=True, type=Path)
    verify_parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "inspect":
        write_json(args.out, profile_template(args.template))
        print(f"wrote template plan: {args.out}")
    elif args.command == "clone":
        created = clone_background_slide(args.template, args.out, args.source_slide, args.count)
        if args.manifest:
            write_json(args.manifest, {
                "schemaVersion": 1,
                "mode": "append-only-template-embedding",
                "template": str(args.template.resolve()),
                "output": str(args.out.resolve()),
                "clonedSlides": created,
            })
        print(f"created {len(created)} appended slide(s): {args.out}")
    else:
        report = verify_template_integrity(args.template, args.output)
        write_json(args.report, report)
        print(f"template integrity: {report['result']}")
        if report["result"] != "pass":
            raise SystemExit(2)


if __name__ == "__main__":
    main()

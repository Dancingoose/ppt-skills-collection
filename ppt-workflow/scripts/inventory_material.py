#!/usr/bin/env python3
"""Extract supported source material into auditable PPT workflow inventory files."""
import argparse
import csv
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
MAX_WEB_BYTES = 5 * 1024 * 1024
MAX_MATERIAL_SOURCES = 16


class WebTextExtractor(HTMLParser):
    ignored_tags = {"script", "style", "noscript", "svg"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored_tags:
            self.ignored_depth += 1

    def handle_endtag(self, tag):
        if tag in self.ignored_tags and self.ignored_depth:
            self.ignored_depth -= 1
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "br"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.ignored_depth and data.strip():
            self.parts.append(data.strip() + " ")

    def text(self):
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts)).strip()


def fetch_web_material(url: str, task_dir: Path, saved_name="source-webpage.html"):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "", [], ["URL source must use an absolute http or https URL."], None
    try:
        request = Request(url, headers={"User-Agent": "ppt-workflow-material-inventory/1.0"})
        with urlopen(request, timeout=20) as response:
            raw = response.read(MAX_WEB_BYTES + 1)
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
    except Exception as exc:
        return "", [], [f"URL fetch failed: {exc}"], None
    if len(raw) > MAX_WEB_BYTES:
        return "", [], [f"URL response exceeds the {MAX_WEB_BYTES} byte safety limit."], None
    if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
        return "", [], [f"URL content type is not supported for text extraction: {content_type}."], None
    try:
        source = raw.decode(charset, errors="replace")
    except LookupError:
        source = raw.decode("utf-8", errors="replace")
    saved = task_dir / saved_name
    saved.write_text(source, encoding="utf-8")
    if content_type == "text/plain":
        return source.strip(), [], [], saved
    parser = WebTextExtractor()
    parser.feed(source)
    text = parser.text()
    warnings = [] if text else [f"URL HTML has no extractable visible text; inspect {saved.name} manually."]
    return text, [], warnings, saved


def plain_text(path: Path):
    return path.read_text(encoding="utf-8", errors="replace"), []


def csv_table_refs(path: Path):
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]
    except OSError as exc:
        return [], [f"CSV extraction failed: {exc}"]
    if not rows:
        return [], ["CSV contains no non-empty rows."]
    header = rows[0]
    data_rows = rows[1:]
    numeric_columns = []
    for index, name in enumerate(header):
        values = []
        for row in data_rows:
            if index >= len(row):
                continue
            value = row[index].strip().replace(",", "")
            try:
                values.append(float(value))
            except ValueError:
                values = []
                break
        if values:
            numeric_columns.append({"name": name, "values": values})
    return [{"name": path.name, "headers": header, "rowCount": len(data_rows), "numericColumns": numeric_columns}], []


def xlsx_cell_text(value):
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def xlsx_table_refs(path: Path):
    try:
        from openpyxl import load_workbook
    except ImportError:
        return [], ["XLSX extraction requires openpyxl; install ppt-workflow/requirements.txt."]
    try:
        raw_workbook = load_workbook(path, read_only=True, data_only=False)
        calculated_workbook = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:
        return [], [f"XLSX extraction failed: {exc}"]

    tables, warnings = [], []
    missing_formula_results = 0
    try:
        for raw_sheet, calculated_sheet in zip(raw_workbook.worksheets, calculated_workbook.worksheets):
            rows = []
            formula_cells = 0
            for raw_row, calculated_row in zip(raw_sheet.iter_rows(), calculated_sheet.iter_rows()):
                raw_values = [cell.value for cell in raw_row]
                if not any(value is not None and str(value).strip() for value in raw_values):
                    continue
                values = []
                for raw_cell, calculated_cell in zip(raw_row, calculated_row):
                    raw_value = raw_cell.value
                    if isinstance(raw_value, str) and raw_value.startswith("="):
                        formula_cells += 1
                        if calculated_cell.value is None:
                            missing_formula_results += 1
                            values.append(raw_value)
                        else:
                            values.append(calculated_cell.value)
                    else:
                        values.append(raw_value)
                rows.append(values)

            if not rows:
                warnings.append(f"XLSX worksheet '{raw_sheet.title}' contains no non-empty rows.")
                continue

            header = [xlsx_cell_text(value) for value in rows[0]]
            data_rows = rows[1:]
            numeric_columns = []
            for index, name in enumerate(header):
                values = []
                for row in data_rows:
                    if index >= len(row):
                        continue
                    value = row[index]
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        values = []
                        break
                    values.append(float(value))
                if values:
                    numeric_columns.append({"name": name, "values": values})
            tables.append({
                "name": f"{path.name}!{raw_sheet.title}",
                "sheet": raw_sheet.title,
                "headers": header,
                "rowCount": len(data_rows),
                "numericColumns": numeric_columns,
                "formulaCells": formula_cells,
            })
    finally:
        raw_workbook.close()
        calculated_workbook.close()

    if missing_formula_results:
        warnings.append(
            f"XLSX contains {missing_formula_results} formula cells without cached results; "
            "recalculate and save it before treating formula results as evidence."
        )
    return tables, warnings


def xlsx_text(path: Path):
    try:
        from openpyxl import load_workbook
    except ImportError:
        return "", ["XLSX extraction requires openpyxl; install ppt-workflow/requirements.txt."]
    try:
        workbook = load_workbook(path, read_only=True, data_only=False)
    except Exception as exc:
        return "", [f"XLSX extraction failed: {exc}"]
    try:
        sheets = []
        for sheet in workbook.worksheets:
            rows = []
            for row in sheet.iter_rows(values_only=True):
                if any(value is not None and str(value).strip() for value in row):
                    rows.append("\t".join(xlsx_cell_text(value) for value in row))
            sheets.append(f"## Worksheet: {sheet.title}\n" + ("\n".join(rows) or "[No non-empty cells]"))
    finally:
        workbook.close()
    return "\n\n".join(sheets), []


def docx_text(path: Path):
    warnings = []
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        return "", [f"DOCX extraction failed: {exc}"]
    paragraphs = []
    for paragraph in root.iter(f"{WORD_NS}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{WORD_NS}t"))
        if text.strip():
            paragraphs.append(text.strip())
    return "\n\n".join(paragraphs), warnings


def pdf_text(path: Path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", ["PDF extraction requires pypdf; install ppt-workflow/requirements.txt."]
    try:
        reader = PdfReader(path)
    except Exception as exc:
        return "", [f"PDF extraction failed: {exc}"]
    pages = []
    for index, page in enumerate(reader.pages, 1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:
            return "", [f"PDF text extraction failed on page {index}: {exc}"]
        pages.append(f"## Page {index}\n" + (text or "[No extractable text]"))
    extracted = "\n\n".join(pages)
    warnings = []
    if not any("[No extractable text]" not in page for page in pages):
        warnings.append("PDF has no extractable text; inspect visually or use OCR before treating it as evidence.")
    return extracted, warnings


def pptx_text(path: Path):
    warnings = []
    try:
        from pptx import Presentation
    except ImportError:
        return "", ["python-pptx is unavailable; run with the workflow virtual environment."]
    try:
        presentation = Presentation(path)
    except Exception as exc:
        return "", [f"PPTX extraction failed: {exc}"]
    chunks, images = [], []
    for slide_index, slide in enumerate(presentation.slides, 1):
        lines = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                value = shape.text.strip()
                if value:
                    lines.append(value)
            if getattr(shape, "shape_type", None) == 13:  # MSO_SHAPE_TYPE.PICTURE
                images.append({"slide": slide_index, "name": shape.name, "source": "embedded picture"})
        chunks.append(f"## Slide {slide_index}\n" + ("\n".join(lines) or "[No extractable text]"))
    return "\n\n".join(chunks), warnings + ([f"Found {len(images)} embedded pictures."] if images else [])


def pptx_image_refs(path: Path):
    try:
        from pptx import Presentation
        presentation = Presentation(path)
    except Exception:
        return []
    refs = []
    for slide_index, slide in enumerate(presentation.slides, 1):
        for shape in slide.shapes:
            if getattr(shape, "shape_type", None) == 13:
                refs.append({"slide": slide_index, "name": shape.name, "description": "Embedded picture"})
    return refs


def standalone_image_refs(path: Path):
    description = "Standalone image material; inspect visually before using it as evidence."
    try:
        from PIL import Image
        with Image.open(path) as image:
            description = f"Standalone image material ({image.width}x{image.height}); inspect visually before using it as evidence."
    except Exception:
        pass
    return [{"name": path.name, "source": str(path.resolve()), "description": description}]


def pdf_image_refs(path: Path, task_dir: Path):
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
    except Exception:
        return []
    output_dir = task_dir / "extracted-images"
    refs = []
    for page_index, page in enumerate(reader.pages, 1):
        for image_index, image in enumerate(page.images, 1):
            name = Path(image.name).name
            suffix = Path(name).suffix.lower() or ".bin"
            output = output_dir / f"page-{page_index:02d}-image-{image_index:02d}{suffix}"
            output_dir.mkdir(parents=True, exist_ok=True)
            output.write_bytes(image.data)
            description = "Image extracted from PDF; inspect visually before using it as evidence."
            try:
                from PIL import Image
                with Image.open(output) as extracted:
                    description = (
                        f"Image extracted from PDF ({extracted.width}x{extracted.height}); "
                        "inspect visually before using it as evidence."
                    )
            except Exception:
                pass
            refs.append({
                "page": page_index,
                "name": name,
                "source": str(output.resolve()),
                "description": description,
            })
    return refs


def extract(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".html", ".htm", ".csv"}:
        return plain_text(path)
    if suffix == ".xlsx":
        return xlsx_text(path)
    if suffix == ".docx":
        return docx_text(path)
    if suffix == ".pdf":
        return pdf_text(path)
    if suffix == ".pptx":
        return pptx_text(path)
    if suffix in IMAGE_SUFFIXES:
        return "", []
    return "", [f"Unsupported source type: {suffix or 'no extension'}"]


def markdown_escape(value: str):
    return value.replace("\r\n", "\n").strip()


def file_material_record(path: Path, task_dir: Path, method: str):
    if not path.is_file():
        return None, [f"Source file does not exist: {path}"]
    text, warnings = extract(path)
    suffix = path.suffix.lower()
    table_refs, table_warnings = (
        csv_table_refs(path) if suffix == ".csv" else
        xlsx_table_refs(path) if suffix == ".xlsx" else
        ([], [])
    )
    warnings.extend(table_warnings)
    image_refs = pptx_image_refs(path) if suffix == ".pptx" else (
        standalone_image_refs(path) if suffix in IMAGE_SUFFIXES else (
            pdf_image_refs(path, task_dir) if suffix == ".pdf" else []
        )
    )
    return {
        "kind": "file", "source": str(path.resolve()), "method": method,
        "format": suffix, "text": text, "images": image_refs, "tables": table_refs,
        "warnings": warnings,
    }, []


def url_material_record(url: str, task_dir: Path, index: int, method: str, total_urls: int):
    saved_name = "source-webpage.html" if total_urls == 1 else f"source-webpage-{index:02d}.html"
    text, image_refs, warnings, saved_source = fetch_web_material(url, task_dir, saved_name)
    record_method = f"{method}; URL fetch"
    if saved_source:
        record_method += f"; saved {saved_source.name}"
    return {
        "kind": "url", "source": url, "method": record_method,
        "format": ".html", "text": text, "images": image_refs, "tables": [],
        "warnings": warnings,
        "savedSource": str(saved_source.resolve()) if saved_source else None,
    }


def aggregate_material_records(records):
    multiple = len(records) > 1
    text = "\n\n".join(
        f"## Source {index}: {record['source']}\n{record['text'] or '[No text could be extracted. Review the original material manually.]'}"
        for index, record in enumerate(records, 1)
    ) if multiple else records[0]["text"]
    images, tables, warnings = [], [], []
    for record in records:
        label = record["source"]
        for item in record["images"]:
            images.append({**item, "materialSource": label})
        for item in record["tables"]:
            tables.append({**item, "materialSource": label})
        warnings.extend(f"{label}: {warning}" for warning in record["warnings"])
    if multiple:
        source, method, source_format = f"{len(records)} supplied sources", "mixed extraction", "mixed"
    else:
        source, method, source_format = records[0]["source"], records[0]["method"], records[0]["format"]
    return {
        "source": source, "method": method, "format": source_format, "text": text,
        "images": images, "tables": tables, "warnings": warnings, "sources": records,
    }


def main():
    parser = argparse.ArgumentParser(description="Create auditable material inventory for a PPT task")
    parser.add_argument("sources", nargs="*", type=Path)
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--method", default="file extraction")
    args = parser.parse_args()
    if not args.sources and not args.url:
        parser.error("provide at least one source file or --url")
    if len(args.sources) + len(args.url) > MAX_MATERIAL_SOURCES:
        parser.error(f"at most {MAX_MATERIAL_SOURCES} source files and URLs may be inventoried together")
    args.task.mkdir(parents=True, exist_ok=True)
    records = []
    for source in args.sources:
        record, errors = file_material_record(source, args.task, args.method)
        if errors:
            parser.error(errors[0])
        records.append(record)
    for index, url in enumerate(args.url, 1):
        records.append(url_material_record(url, args.task, index, args.method, len(args.url)))
    inventory = aggregate_material_records(records)
    source_label, method, text = inventory["source"], inventory["method"], inventory["text"]
    image_refs, table_refs, warnings = inventory["images"], inventory["tables"], inventory["warnings"]
    source_lines = "\n".join(
        f"- {'URL' if record['kind'] == 'url' else 'File'}: {record['source']}\n"
        f"  - Extraction method: {record['method']}"
        for record in records
    )
    (args.task / "material-inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    warning_lines = "\n".join(f"- {warning}" for warning in warnings) or "- None"
    image_lines = "\n".join(
        f"- {'Slide ' + str(item['slide']) + ': ' if item.get('slide') else ''}{item['name']} "
        f"({item['description']})" + (f" — {item['source']}" if item.get("source") else "")
        for item in image_refs
    ) or "- None detected"
    table_lines = "\n".join(
        f"- {table['name']}: {table['rowCount']} data rows; headers: {', '.join(table['headers'])}; "
        f"numeric columns: {', '.join(column['name'] for column in table['numericColumns']) or 'none'}"
        + (f"; source: {table['materialSource']}" if table.get('materialSource') else "")
        for table in table_refs
    ) or "- None detected"
    content = f"""# Content Inventory

## Source Files
- {len(records)} source(s) inventoried
{source_lines}
- Structured inventory: material-inventory.json

## Extracted Source Content
{markdown_escape(text) or '[No text could be extracted. Review the original material manually.]'}

## Core Message
[To be confirmed from the material with the creator.]

## Image Resources
{image_lines}

## Structured Tables
{table_lines}

## Data Points
[Extract claims with source URLs or citations before using a data layout.]

## Page and Chapter Plan
[Create after confirming the audience, decision, and core message.]

## Extraction Warnings
{warning_lines}
"""
    (args.task / "content-inventory.md").write_text(content, encoding="utf-8")
    print(f"Wrote {args.task / 'content-inventory.md'}")
    print(f"Wrote {args.task / 'material-inventory.json'}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()

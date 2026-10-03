r"""Generate an engineering PDF from saved CAD and a YAML report manifest.

    .venv\Scripts\python tools\engineering_report.py reports\naca_lewis_16in_ramjet.yaml

Paths in the manifest resolve from the project root. --build regenerates the
Python model first. Report data does not override the model's geometry.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import importlib.util
from importlib import metadata as package_metadata
import json
import math
from pathlib import Path
import subprocess
import sys
from xml.sax.saxutils import escape

import pymupdf as fitz
import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
NAVY = colors.HexColor("#142C42")
BLUE = colors.HexColor("#087F9B")
MUTED = colors.HexColor("#526778")
PALE = colors.HexColor("#EDF4F7")
WIDTH, HEIGHT = A4
MARGIN = 42
BODY_WIDTH = WIDTH - 2 * MARGIN
UNIT_MM = {"mm": 1.0, "in": 25.4, "m": 1000.0}


class UniqueLoader(yaml.SafeLoader):
    """Safe YAML with duplicate-key rejection, including merged mappings."""


def unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_config(path, require_step=True):
    cfg = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=UniqueLoader)
    if not isinstance(cfg, dict) or cfg.get("schema_version") != 1:
        raise ValueError("Report requires schema_version: 1")
    for key in ("title", "model", "renders", "drawings"):
        if not cfg.get(key):
            raise ValueError(f"Missing report field: {key}")
    for key in ("source", "step"):
        path_value = ROOT / cfg["model"][key]
        if (key == "source" or require_step) and not path_value.is_file():
            raise ValueError(f"Missing {key}: {path_value}")
    names = [item["id"] for item in cfg["renders"]]
    if len(set(names)) != len(names) or any(Path(n).name != n for n in names):
        raise ValueError("Render IDs must be unique simple filenames")
    source_ids = {item["id"] for item in cfg.get("sources", [])}
    for item in cfg.get("specifications", []):
        if item.get("source") and item["source"] not in source_ids:
            raise ValueError(f"Unknown specification source: {item['source']}")
    return cfg


def load_model(path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scalar(value, module):
    """A literal mm coordinate or a named model constant with explicit units."""
    if isinstance(value, dict):
        parameter, unit = value["parameter"], value.get("unit", "mm")
        if parameter.startswith("_") or unit not in UNIT_MM:
            raise ValueError(f"Invalid parameter/unit: {parameter}, {unit}")
        value = getattr(module, parameter) * UNIT_MM[unit]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Expected a finite numeric coordinate, got {value!r}")
    return float(value)


def point(values, module):
    if len(values) != 3:
        raise ValueError("Drawing points require three coordinates")
    return tuple(scalar(value, module) for value in values)


def run(args, **kwargs):
    print("Running " + " ".join(str(a) for a in args[2:4]), flush=True)
    result = subprocess.run(args, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                            capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr)[-6000:])
    return result.stdout


def render_views(cfg, step, work):
    listed = json.loads(run([sys.executable, "-m", "cadgen.cli", "step", "snapshot",
                             str(step), "--mode", "list"]))
    refs = {item["name"]: item["ref"] for item in listed}
    outputs = {}
    for view in cfg["renders"]:
        target = work / (view["id"] + ".png")
        args = [sys.executable, "-m", "cadgen.cli", "step", "snapshot", str(step), str(target),
                "--width", "2400", "--height", "1400", "--camera", view.get("camera", "210:20"),
                "--display", view.get("display", "render")]
        if view.get("mode") == "section":
            args.extend(["--mode", "section", "--section", view.get("section", "XY")])
        for name in view.get("hide", []):
            if name not in refs:
                raise ValueError(f"Unknown render part: {name}")
            args.extend(["--hide", refs[name]])
        run(args)
        outputs[view["id"]] = target
        print(f"Rendered {view['id']}", flush=True)
    return outputs


def dimensions(view, entries, module):
    for dim in entries:
        kind = dim["type"]
        if kind == "overall":
            view.overall()
        elif kind == "linear":
            view.dim(point(dim["p1"], module), point(dim["p2"], module),
                     orientation=dim.get("orientation"), offset=dim.get("offset"))
        elif kind in ("diameter", "radius"):
            getattr(view, kind)(point(dim["center"], module), scalar(dim["radius"], module),
                               angle=dim.get("angle", 45))
        elif kind == "note":
            view.note(dim["text"], point(dim["at"], module), offset=tuple(dim.get("offset", [10, 10])))
        else:
            raise ValueError(f"Unknown dimension type: {kind}")


def make_drawings(cfg, shape, parts, module, output):
    from cadgen import build123d as bd
    from cadgen.eng_drawing import Sheet, eng_drawing
    by_label = {part.label: part for part in parts}

    @eng_drawing(out=str(output))
    def engineering_drawings():
        sheets = []
        for definition in cfg["drawings"]:
            selected = shape
            if definition.get("parts"):
                missing = set(definition["parts"]) - by_label.keys()
                if missing:
                    raise ValueError(f"Unknown drawing parts: {sorted(missing)}")
                selected = bd.Compound(children=[by_label[name] for name in definition["parts"]])
            sheet = Sheet(definition.get("size", "A3"), scale=definition["scale"],
                          title=definition["title"], part_number=cfg.get("document_id", ""),
                          revision=cfg.get("revision", "A"), author="CadStudio", units="mm",
                          material="See report", text_height=2.8, notes=definition.get("notes", []))
            if definition.get("views"):
                views = {item["name"]: sheet.view(selected, item["name"], at=tuple(item["at"]),
                                                 hidden=item.get("hidden", False), centre_marks=False,
                                                 label=item.get("label")) for item in definition["views"]}
            else:
                top, front, right = sheet.three_views(selected, hidden=False, centre_marks=False)
                views = {"top": top, "front": front, "right": right}
            for name, entries in definition.get("dimensions", {}).items():
                if name not in views:
                    raise ValueError(f"Dimension refers to absent view: {name}")
                dimensions(views[name], entries, module)
            sheets.append(sheet)
        return sheets

    engineering_drawings()


class Report:
    def __init__(self, output, cfg):
        self.pdf = canvas.Canvas(str(output), pagesize=A4, pageCompression=1)
        self.cfg, self.page = cfg, 0
        self.pdf.setTitle(cfg["title"] + " - Engineering report")
        self.pdf.setAuthor("CadStudio")
        self.style = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=15, textColor=NAVY)

    def paragraph(self, text, x, y, width=BODY_WIDTH, size=10, colour=NAVY):
        style = ParagraphStyle("block", parent=self.style, fontSize=size, leading=size * 1.5, textColor=colour)
        paragraph = Paragraph(escape(str(text)).replace("\n", "<br/>"), style)
        _, height = paragraph.wrap(width, HEIGHT)
        if y - height < 55:
            raise ValueError("Report text exceeds page; split the content into more pages")
        paragraph.drawOn(self.pdf, x, y - height)
        return y - height - 9

    def start(self, title, subtitle=""):
        self.page += 1
        pdf = self.pdf
        pdf.setFillColor(BLUE)
        pdf.rect(MARGIN, HEIGHT - 43, 32, 4, fill=1, stroke=0)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(MARGIN + 43, HEIGHT - 43, "CADSTUDIO / ENGINEERING REPORT")
        y = self.paragraph(title, MARGIN, HEIGHT - 73, size=22)
        if subtitle:
            y = self.paragraph(subtitle, MARGIN, y, size=10, colour=MUTED)
        pdf.setStrokeColor(colors.HexColor("#D7E3EA"))
        pdf.line(MARGIN, 42, WIDTH - MARGIN, 42)
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(MUTED)
        pdf.drawString(MARGIN, 27, f"{self.cfg.get('document_id', '')} / REV {self.cfg.get('revision', 'A')}")
        pdf.drawRightString(WIDTH - MARGIN, 27, f"{self.page:02d}")
        return y - 10

    def image(self, path, y, height):
        self.pdf.drawImage(ImageReader(str(path)), MARGIN, y - height, BODY_WIDTH, height,
                           preserveAspectRatio=True, anchor="c", mask="auto")
        return y - height - 8

    def table(self, rows, widths, y):
        cells = [[Paragraph(escape(str(cell)), ParagraphStyle("cell", parent=self.style,
                  fontSize=8, leading=11)) for cell in row] for row in rows]
        table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.7, BLUE),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#D7E3EA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        _, height = table.wrap(BODY_WIDTH, HEIGHT)
        if y - height < 55:
            raise ValueError("Report table exceeds page; shorten or split the manifest table")
        table.drawOn(self.pdf, MARGIN, y - height)
        return y - height - 18

    def end(self):
        self.pdf.showPage()


def component_rows(cfg, parts):
    rows = [["Component", "Length / mm", "Volume / L", "Material", "Mass / kg"]]
    assigned = cfg.get("part_materials", {})
    materials = cfg.get("materials", {})
    known_labels = {part.label for part in parts}
    if set(assigned) - known_labels:
        raise ValueError("Material assignment names a missing component")
    for part in parts:
        material_id = assigned.get(part.label)
        material = materials.get(material_id) if material_id else None
        if material_id and material is None:
            raise ValueError(f"Unknown material ID: {material_id}")
        density = material.get("density_kg_m3") if material else None
        if density is not None and (isinstance(density, bool) or not isinstance(density, (int, float))
                                    or not math.isfinite(density) or density <= 0):
            raise ValueError("Material density must be finite and positive in kg/m3")
        rows.append([part.label.replace("_", " "), f"{part.bounding_box().size.X:.1f}",
                     f"{part.volume / 1e6:.3f}", material.get("name", material_id) if material else "Unknown",
                     f"{part.volume * density * 1e-9:.3f}" if density else "Unknown"])
    return rows


def write_report(cfg, shape, parts, module, renders, output, fingerprints):
    report = Report(output, cfg)
    y = report.start(cfg["title"], cfg.get("subtitle", ""))
    y = report.paragraph(cfg.get("summary", ""), MARGIN, y)
    y = report.image(renders[cfg["renders"][0]["id"]], y, 275)
    bbox = shape.bounding_box().size
    y = report.table([["MODEL LENGTH", "MAXIMUM ENVELOPE", "COMPONENTS"],
                      [f"{bbox.X:,.1f} mm", f"{bbox.Y:,.1f} x {bbox.Z:,.1f} mm", str(len(parts))]],
                     [BODY_WIDTH / 3] * 3, y)
    y = report.paragraph(cfg.get("status", "Study reconstruction"), MARGIN, y, colour=BLUE)
    report.paragraph("Prepared " + date.today().isoformat() + ". Dimensions are in millimetres unless stated. "
                     "The appended A3 sheets retain their native drawing scale.", MARGIN, y, size=9, colour=MUTED)
    report.end()

    extra = cfg["renders"][1:]
    for index in range(0, len(extra), 2):
        y = report.start("Visual inspection", "Views generated from the saved STEP geometry")
        for view in extra[index:index + 2]:
            y = report.paragraph(view.get("title", view["id"]), MARGIN, y, size=12, colour=BLUE)
            y = report.image(renders[view["id"]], y, 205)
            y = report.paragraph(view.get("caption", ""), MARGIN, y, size=9, colour=MUTED)
        report.end()

    y = report.start("Dimensions and components", "Model measurements and reference values")
    rows = [["Specification", "Value", "Basis"]]
    for item in cfg.get("specifications", []):
        value = item.get("value", "Unknown")
        if isinstance(value, dict):
            mm_value = scalar(value, module)
            unit = item.get("unit", "mm")
            if unit not in UNIT_MM:
                raise ValueError(f"Unknown specification unit: {unit}")
            value = f"{mm_value / UNIT_MM[unit]:g} {unit}"
        rows.append([item["label"], value, item.get("basis", "")])
    if len(rows) > 1:
        y = report.table(rows, [BODY_WIDTH * .39, BODY_WIDTH * .22, BODY_WIDTH * .39], y)
    y = report.paragraph("Component inventory", MARGIN, y, size=12, colour=BLUE)
    y = report.table(component_rows(cfg, parts), [BODY_WIDTH * .34, BODY_WIDTH * .16,
                     BODY_WIDTH * .16, BODY_WIDTH * .17, BODY_WIDTH * .17], y)
    report.paragraph("Volumes describe the simplified CAD solids. Mass is calculated only when a component has "
                     "an explicit material density; unknown entries have no mass estimate.", MARGIN, y, size=9, colour=MUTED)
    report.end()

    y = report.start("Sources and modelling notes", "Traceable inputs, assumptions and saved revision")
    for source in cfg.get("sources", []):
        y = report.paragraph(f"[{source['id']}] {source['title']}", MARGIN, y, size=10)
        if source.get("locator"):
            y = report.paragraph(source["locator"], MARGIN, y, size=9, colour=MUTED)
    y = report.paragraph("Modelling assumptions", MARGIN, y - 6, size=12, colour=BLUE)
    for note in cfg.get("assumptions", []):
        y = report.paragraph("- " + note, MARGIN, y, size=9)
    y = report.paragraph("Document traceability", MARGIN, y - 6, size=12, colour=BLUE)
    for key, value in fingerprints.items():
        y = report.paragraph(f"{key}: {value[:24]}...", MARGIN, y, size=8, colour=MUTED)
    report.paragraph("Full hashes, geometry checks and drawing-sheet sizes are recorded in the report's adjacent JSON file.",
                     MARGIN, y, size=9, colour=MUTED)
    report.end()
    report.pdf.save()


def assemble_pdf(body, drawings, output):
    with fitz.open(body) as document, fitz.open(drawings) as sheets:
        document.insert_pdf(sheets)
        document.set_toc([[1, "Model overview", 1], [1, "Engineering drawings", document.page_count - sheets.page_count + 1]])
        temporary = output.with_suffix(".partial.pdf")
        document.save(temporary, garbage=4, deflate=True)
    temporary.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--build", action="store_true", help="Regenerate the declared Python model before reporting")
    parser.add_argument("--reuse-renders", action="store_true", help="Reuse only renders matching the STEP and manifest hashes")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    cfg = load_config(manifest, require_step=not args.build)
    source, step = (ROOT / cfg["model"][key] for key in ("source", "step"))
    if args.build:
        run([sys.executable, str(source)])
    module = load_model(source)
    from cadgen import read_step
    shape = read_step(str(step))
    parts = list(shape.leaves)
    if not parts or not shape.is_valid or any(p.volume <= 0 for p in parts):
        raise ValueError("The saved STEP must contain valid, positive-volume components")
    fingerprints = {"STEP SHA256": digest(step), "SOURCE SHA256": digest(source), "MANIFEST SHA256": digest(manifest)}
    key = hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode()).hexdigest()[:16]
    work = ROOT / "tmp" / "reports" / source.stem / key
    work.mkdir(parents=True, exist_ok=True)
    renders = {item["id"]: work / (item["id"] + ".png") for item in cfg["renders"]}
    if not args.reuse_renders or not all(p.is_file() for p in renders.values()):
        renders = render_views(cfg, step, work)
    drawing_pdf, body_pdf = work / "drawings.pdf", work / "body.pdf"
    make_drawings(cfg, shape, parts, module, drawing_pdf)
    output = args.output.resolve() if args.output else ROOT / "output" / "pdf" / (source.stem + "_engineering_report.pdf")
    if output.suffix.lower() != ".pdf":
        raise ValueError("Report output must have a .pdf extension")
    output.parent.mkdir(parents=True, exist_ok=True)
    write_report(cfg, shape, parts, module, renders, body_pdf, fingerprints)
    assemble_pdf(body_pdf, drawing_pdf, output)
    with fitz.open(output) as document:
        metadata = {"schema_version": 1, "model": source.stem, "cadgen_version": package_metadata.version("cadgen"),
                    "hashes": fingerprints, "component_count": len(parts), "valid_geometry": True,
                    "volume_mm3": shape.volume, "page_count": document.page_count,
                    "pages_mm": [[round(p.rect.width * 25.4 / 72, 2), round(p.rect.height * 25.4 / 72, 2)] for p in document]}
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {output} ({metadata['page_count']} pages)", flush=True)


if __name__ == "__main__":
    main()

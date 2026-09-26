"""Visual verification loop: render a model from several views into one sheet, and optionally
score its side silhouette against a reference picture.

    .venv\\Scripts\\python tools\\render_check.py models\\STEP\\tsirkon.step
    .venv\\Scripts\\python tools\\render_check.py models\\STEP\\tsirkon.step --ref ref.jpg --ref-box 60,560,1330,640

Outputs tmp/check/<model>_sheet.png (iso, rear, side, top, section views) and, with --ref,
tmp/check/<model>_overlay.png: grey = both, red = model only, cyan = reference only, plus the
silhouette IoU and the worst radius mismatch along the length. --ref-box is the reference
object's bounding box in pixels (x0,y0,x1,y1), nose/front at x0; the model is fitted to it by
length, so the score measures shape, not scale. Models are Y-up (as in SolidWorks).
"""
import argparse
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
VIEWS = [("iso", ["--camera", "210:20"]), ("rear 3/4", ["--camera", "30:20"]), ("side", ["--camera", "0:90"]),
         ("top", ["--camera", "0:0"]), ("section (XY)", ["--mode", "section", "--camera", "0:90"])]


def snapshot(step, out, args, size=(1600, 1000)):
    cmd = [sys.executable, "-m", "cadgen.cli", "step", "snapshot", str(step.resolve()), str(out.resolve()),
           "--width", str(size[0]), "--height", str(size[1]), *args]
    subprocess.run(cmd, cwd=ROOT / "models", check=True, capture_output=True)
    return Image.open(out).convert("RGB")


def hide_args(step, names):
    """--hide flags for part labels (the snapshot CLI wants occurrence refs such as #o1.1)."""
    if not names:
        return []
    cmd = [sys.executable, "-m", "cadgen.cli", "step", "snapshot", str(step.resolve()), "--mode", "list"]
    occ = json.loads(subprocess.run(cmd, cwd=ROOT / "models", check=True, capture_output=True, text=True).stdout)
    refs = {o["name"]: o["ref"] for o in occ}
    missing = [n for n in names if n not in refs]
    if missing:
        raise SystemExit(f"unknown parts {missing}; available: {sorted(refs)}")
    return [flag for n in names for flag in ("--hide", refs[n])]


def mask(img, box=None, tol=40):
    """Foreground mask (L image): pixels that differ from the background colour sampled at the corners."""
    if box:
        img = img.crop(box)
    w, h = img.size
    bg = [img.getpixel(p) for p in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2))]
    bg = tuple(sorted(c[i] for c in bg)[1] for i in range(3))
    diff = ImageChops.difference(img, Image.new("RGB", img.size, bg)).convert("L")
    m = diff.point(lambda v: 255 if v > tol else 0)
    return m.crop(m.getbbox()) if box is None and m.getbbox() else m


def filled(m):
    """Fill each column between its first and last foreground pixel (line drawings -> solid silhouettes)."""
    out = Image.new("L", m.size)
    draw = ImageDraw.Draw(out)
    for x, ext in enumerate(profile(m)):
        if ext:
            draw.line([(x, ext[0]), (x, ext[1])], fill=255)
    return out


def profile(m):
    """Per column (top, bottom) extent of the mask, or None where empty."""
    w, h = m.size
    px = m.load()
    cols = []
    for x in range(w):
        ys = [y for y in range(h) if px[x, y]]
        cols.append((ys[0], ys[-1]) if ys else None)
    return cols


def overlay(model_side, ref_img, box, length_mm, out, ref_tol=40):
    mm_ = filled(mask(model_side))
    rm = mask(ref_img, box, tol=ref_tol)
    rm = filled(rm.crop(rm.getbbox()))
    scale = rm.width / mm_.width  # fit by length
    mm_ = mm_.resize((rm.width, max(1, round(mm_.height * scale))))
    h = max(mm_.height, rm.height)
    canvas_m, canvas_r = Image.new("L", (rm.width, h)), Image.new("L", (rm.width, h))
    canvas_m.paste(mm_, (0, (h - mm_.height) // 2))
    canvas_r.paste(rm, (0, (h - rm.height) // 2))
    both = ImageChops.multiply(canvas_m, canvas_r)
    union = ImageChops.lighter(canvas_m, canvas_r)
    iou = sum(both.histogram()[255:]) / max(1, sum(union.histogram()[255:]))
    rgb = Image.merge("RGB", (canvas_m, canvas_r, canvas_r))  # red = model only, cyan = ref only
    rgb.paste((150, 150, 150), mask=both)
    # radius mismatch per station (half of the height difference), in mm when the length is given
    mm_per_px = length_mm / rm.width if length_mm else None
    worst = (0, 0)
    for x, (a, b) in enumerate(zip(profile(canvas_m), profile(canvas_r))):
        if a and b:
            d = abs((a[1] - a[0]) - (b[1] - b[0])) / 2
            worst = max(worst, (d, x))
    big = rgb.resize((rgb.width * 2, rgb.height * 2), Image.NEAREST)
    big.save(out)
    d, x = worst
    where = f"{x * mm_per_px:.0f} mm from the front" if mm_per_px else f"x = {x} px"
    size = f"{d * mm_per_px:.0f} mm" if mm_per_px else f"{d:.1f} px"
    return iou, f"worst radius mismatch {size} at {where}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", type=pathlib.Path)
    ap.add_argument("--ref", type=pathlib.Path, help="reference image (side view)")
    ap.add_argument("--ref-box", help="x0,y0,x1,y1 of the object in the reference image")
    ap.add_argument("--ref-rotate", type=int, default=0, help="rotate the cropped reference CCW (90: nose-up -> nose-left)")
    ap.add_argument("--ref-tol", type=int, default=40, help="background tolerance for the reference (lower for dark objects on dark backgrounds)")
    ap.add_argument("--ref-flip", action="store_true", help="mirror the cropped reference (its nose points right)")
    ap.add_argument("--length", type=float, help="model length in mm (reports mismatch in mm)")
    ap.add_argument("--hide", default="", help="comma-separated part labels to hide in all renders")
    args = ap.parse_args()
    out_dir = ROOT / "tmp" / "check"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = args.step.stem

    hide = hide_args(args.step, [n for n in args.hide.split(",") if n])
    tiles = []
    for label, view_args in VIEWS:
        img = snapshot(args.step, out_dir / f"{name}_{label.split()[0]}.png", view_args + hide)
        img.thumbnail((800, 500))
        tile = Image.new("RGB", (800, 530), "white")
        tile.paste(img, (0, 30))
        ImageDraw.Draw(tile).text((8, 8), f"{name}: {label}", fill=(200, 0, 0))
        tiles.append(tile)
    sheet = Image.new("RGB", (1600, 530 * ((len(tiles) + 1) // 2)), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 2) * 800, (i // 2) * 530))
    sheet_path = out_dir / f"{name}_sheet.png"
    sheet.save(sheet_path)
    print("sheet:", sheet_path)

    if args.ref:
        box = tuple(int(v) for v in args.ref_box.split(",")) if args.ref_box else None
        side = snapshot(args.step, out_dir / f"{name}_side_wide.png", ["--camera", "0:90", *hide], size=(3200, 900))
        ref = Image.open(args.ref).convert("RGB")
        ref = ref.crop(box) if box else ref
        ref = ref.rotate(args.ref_rotate, expand=True) if args.ref_rotate else ref
        ref = ref.transpose(Image.FLIP_LEFT_RIGHT) if args.ref_flip else ref
        iou, worst = overlay(side, ref, None, args.length, out_dir / f"{name}_overlay.png", args.ref_tol)
        print(f"overlay: {out_dir / f'{name}_overlay.png'}  silhouette IoU {iou:.3f}; {worst}")


if __name__ == "__main__":
    main()

r"""Fill a LaTeX template from Python and compile it to PDF.

    .venv\Scripts\python reports\latex\naca_lewis_16in_ramjet.py

A report script computes its numbers, saves its plots with save_figure() and
calls build(). Templates stay valid-looking LaTeX: Jinja2 reads \VAR{...},
\BLOCK{...} and \#{...}. Values are LaTeX-escaped unless marked with |raw.
Compiling needs latexmk and lualatex on PATH (TeX Live or MiKTeX).
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess

import jinja2

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "reports" / "latex"
INK, GREY, LIGHT = "black", "0.45", "0.9"
TEXT_WIDTH_IN = 150 / 25.4  # cadstudio.cls text block; a figure saved narrower than this is included unscaled
ESCAPES = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


class Raw(str):
    """LaTeX source that is inserted into a template without escaping."""


def tex_escape(value):
    if isinstance(value, Raw):
        return value
    return Raw(re.sub(r"[\\&%$#_{}~^]", lambda match: ESCAPES[match.group()], str(value)))


def environment(template_dir=TEMPLATES):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)), undefined=jinja2.StrictUndefined,
        block_start_string=r"\BLOCK{", block_end_string="}",
        variable_start_string=r"\VAR{", variable_end_string="}",
        comment_start_string=r"\#{", comment_end_string="}",
        trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True, finalize=tex_escape)
    env.filters["raw"] = Raw
    return env


def tex_font(filename):
    """Path of a font file shipped with the TeX distribution, or None."""
    if not shutil.which("kpsewhich"):
        return None
    found = subprocess.run(["kpsewhich", filename], capture_output=True, text=True).stdout.strip()
    return found or None


def plot_style():
    """Matplotlib defaults for journal-style figures: Latin Modern, black ink, boxed axes, inward ticks."""
    import logging
    import matplotlib
    from matplotlib import font_manager
    logging.getLogger("fontTools").setLevel(logging.ERROR)   # Latin Modern's zero timestamps are harmless
    fonts = [tex_font(f"lmroman10-{shape}.otf") for shape in ("regular", "italic", "bold")]
    if all(fonts):
        for path in fonts:
            font_manager.fontManager.addfont(path)
    serif = (["Latin Modern Roman"] if all(fonts) else []) + ["DejaVu Serif"]
    ticks = {f"{axis}tick.{key}": value for axis in "xy" for key, value in {
        "direction": "in", "minor.visible": True, "major.size": 4, "minor.size": 2, "major.width": 0.6,
        "minor.width": 0.4, "labelsize": 9}.items()}
    matplotlib.rcParams.update({
        "font.family": "serif", "font.serif": serif, "font.size": 10, "mathtext.fontset": "cm",
        "axes.linewidth": 0.6, "axes.labelsize": 10, "axes.prop_cycle": matplotlib.cycler(color=[INK]),
        "xtick.top": True, "ytick.right": True, **ticks, "lines.linewidth": 1.0, "lines.markersize": 5,
        "legend.frameon": False, "legend.fontsize": 9, "legend.handlelength": 2.8,
        "figure.constrained_layout.use": True, "pdf.fonttype": 42, "savefig.transparent": True,
    })


def save_figure(fig, path):
    """Save a Matplotlib figure as vector PDF and close it."""
    import matplotlib.pyplot as plt
    fig.savefig(path)
    plt.close(fig)
    return Path(path)


def log_errors(log):
    """The error lines of a LaTeX log, each with the two lines that follow it."""
    lines = log.splitlines()
    hits = [i for i, line in enumerate(lines) if line.startswith("!") or re.match(r".+:\d+: ", line)]
    return "\n".join("\n".join(lines[i:i + 3]) for i in hits[:8]) or "\n".join(lines[-30:])


def build(template, context, output, work, compile_pdf=True):
    """Render reports/latex/<template> into work/, compile it there and copy the PDF to output.

    Figures and images named in the template resolve from work/. With compile_pdf=False only the
    .tex file is written, for editing or compiling elsewhere.
    """
    work, output = Path(work), Path(output)
    work.mkdir(parents=True, exist_ok=True)
    tex = work / (output.stem + ".tex")
    tex.write_text(environment().get_template(template).render(**context), encoding="utf-8")
    if not compile_pdf:
        print(f"LaTeX source: {tex}", flush=True)
        return tex
    if not shutil.which("latexmk") or not shutil.which("lualatex"):
        raise RuntimeError("latexmk and lualatex are required on PATH; install TeX Live or MiKTeX, "
                           "or pass --tex-only to write the LaTeX source alone")
    env = dict(os.environ, TEXINPUTS=os.pathsep.join([str(TEMPLATES), os.environ.get("TEXINPUTS", "")]))
    result = subprocess.run(["latexmk", "-lualatex", "-interaction=nonstopmode", "-halt-on-error",
                             "-file-line-error", tex.name], cwd=work, env=env, text=True,
                            encoding="utf-8", errors="replace", capture_output=True)
    if result.returncode:
        log = tex.with_suffix(".log")
        raise RuntimeError(f"LaTeX failed ({log}):\n" + log_errors(
            log.read_text(encoding="utf-8", errors="replace") if log.is_file() else result.stdout))
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tex.with_suffix(".pdf"), output)
    print(f"Report: {output}", flush=True)
    return output

# LaTeX reports

An optional second report path for documents that carry analysis: equations,
plots, numbered tables and cross-references. The
[YAML-driven engineering report](engineering-reports.md) stays the default for
renders, component tables and drawing sheets and needs no TeX installation.

## How it is put together

Python computes and LaTeX typesets. Neither generates the other's content:

| File | Role |
| --- | --- |
| `tools/latex_report.py` | Fills a template, runs `latexmk`, reports LaTeX errors, sets the plot style |
| `reports/latex/cadstudio.cls` | The look: a research-memorandum article in Latin Modern with a report-number title block |
| `reports/latex/<report>.tex` | The document: prose, equations and table layout, with placeholders for values |
| `reports/latex/<report>.py` | The numbers: reads the model source, calculates, saves plots, calls `build()` |

Every number in the PDF comes from the script, so a change to the model
constants flows through to the tables, plots and prose on the next run. The
`.tex` template is ordinary LaTeX that an editor highlights normally.

## Requirements

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
```

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Compiling needs `latexmk` and `lualatex` on `PATH`. On Ubuntu install TeX Live with
`sudo apt install latexmk texlive-luatex texlive-latex-recommended texlive-fonts-recommended lmodern`.
On Windows use [TeX Live](https://tug.org/texlive/) or [MiKTeX](https://miktex.org/). The class
uses Latin Modern, the LaTeX default, which both distributions provide. The first LuaLaTeX run
builds a font cache and can take a few minutes; later runs take seconds.

## Generate the sample

```powershell
.venv\Scripts\python reports\latex\naca_lewis_16in_ramjet.py
```

```bash
.venv/bin/python reports/latex/naca_lewis_16in_ramjet.py
```

This writes `output/pdf/naca_lewis_16in_ramjet_flow_path.pdf`: flow-area
distribution from the model's Table I coordinates, conical-shock and
pressure-recovery estimates at the two free-jet Mach numbers, and the chamber
Mach number over the exit-plug travel. They are ideal one-dimensional
estimates from the CAD geometry, not test data.

- `--tex-only` writes the `.tex` and figures without compiling, so no TeX
  installation is needed. Compile it elsewhere with `cadstudio.cls` alongside.
- `--no-render` leaves out the CAD image. Otherwise the exterior view is
  rendered from the saved STEP once and reused until the STEP changes.
- `--output <path>.pdf` chooses another destination.

Intermediate files (`.tex`, figures, LaTeX log) are kept in ignored
`tmp/latex/<model>/`.

## Write another report

Copy the sample `.py` and `.tex` pair. In the script, build a `context`
dictionary and call:

```python
build("my_report.tex", context, output_pdf, work_dir)
```

Template placeholders use LaTeX-friendly delimiters:

```latex
\title{\VAR{title}}
The chamber area is \qty{\VAR{"%.0f"|format(chamber_cm2)}}{\centi\metre\squared}.
\BLOCK{for row in stations}
  \VAR{row.label} & \VAR{"%.1f"|format(row.x_mm)} \\
\BLOCK{endfor}
```

- Inserted values are LaTeX-escaped, so `profile_builder/` or `54 %` from a
  manifest is safe. Use `\VAR{value|raw}` for a value that is LaTeX source.
- A missing value stops the build instead of leaving a gap.
- Placeholders are read everywhere, including LaTeX comments.
- Put `{}` between a control word and a placeholder: `\quad{}\VAR{title}`.

`plot_style()` sets journal-style Matplotlib defaults: Latin Modern text,
Computer Modern maths, black lines told apart by dash pattern, boxed axes and
inward ticks. Save plots with `save_figure()` no wider than `TEXT_WIDTH_IN`
and include them unscaled (`\includegraphics{duct.pdf}`); they stay vector
and their text matches the document's sizes.

The class is a plain `article` with a report-number title block (`\title`,
`\subtitle`, `\documentid`, `\revision`, `\maketitle`), a running head, a
two-column `nomenclature` list and `\tablenote{...}`. `siunitx`, `booktabs`,
`tabularx`, `float` and `multicol` are loaded; references use the standard
`thebibliography` and `\cite`. To append cadgen drawing sheets, add `\usepackage{pdfpages}` and
`\includepdf[pages=-,fitpaper]{drawings.pdf}` to the template.

## Verify

```powershell
.venv\Scripts\python -m unittest discover -s tests   # Windows
```

```bash
.venv/bin/python -m unittest discover -s tests       # Ubuntu
```

The tests cover escaping, the template syntax and the sample's shock and
area relations against textbook values. They do not compile LaTeX; review
the PDF after changing a template or the class.

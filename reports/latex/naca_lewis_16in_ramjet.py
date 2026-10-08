r"""Sample LaTeX report: flow-path analysis of the NACA Lewis 16-inch ramjet.

    .venv\Scripts\python reports\latex\naca_lewis_16in_ramjet.py

Reads the duct coordinates from the model source, applies textbook one-dimensional
gas dynamics, saves the plots and fills naca_lewis_16in_ramjet.tex. The values are
ideal estimates from the CAD model's tables, not test data. --tex-only skips the
LaTeX compile; --no-render leaves out the CAD image.
"""
from __future__ import annotations

import argparse
from datetime import date
from functools import lru_cache
from math import atan, cos, degrees, pi, radians, sin, sqrt, tan
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize_scalar

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from engineering_report import digest, load_config, load_model, render_views
from latex_report import GREY, INK, LIGHT, build, plot_style, save_figure

MANIFEST = ROOT / "reports" / "naca_lewis_16in_ramjet.yaml"
IN = 25.4
GAMMA_AIR, GAMMA_HOT = 1.4, 1.3   # cold inlet air; assumed mean value for the combustion products
CONE_HALF_ANGLE = 23.0            # Table I: 46 degree included spike cone
FREE_JET_MACH = {1.35: 2.63, 1.73: 4.27}   # Table I: spike-tip projection ahead of the lip, in
PLUG_AREA = (0.51, 0.74)          # reported exit area as a fraction of the chamber area
FIGURE_WIDTH = 4.9                # in; narrower than the text block, as in a journal column
METHOD_REFERENCES = [
    {"id": "AMES1135", "title": "Ames Research Staff: Equations, tables, and charts for compressible flow. "
                                "NACA Report 1135, 1953.", "locator": ""},
    {"id": "TM1933", "title": "Taylor, G. I., and Maccoll, J. W.: The air pressure on a cone moving at high "
                              "speeds. Proceedings of the Royal Society of London A, vol. 139, 1933, pp. 278-311.",
     "locator": ""},
]


# --- gas dynamics -----------------------------------------------------------------------------

def total_temperature(mach, g=GAMMA_AIR):
    return 1 + (g - 1) / 2 * mach ** 2


def total_pressure(mach, g=GAMMA_AIR):
    return total_temperature(mach, g) ** (g / (g - 1))


def shock_recovery(mach_n, g=GAMMA_AIR):
    """Total-pressure ratio across a shock with upstream normal Mach number mach_n."""
    density = (g + 1) * mach_n ** 2 / ((g - 1) * mach_n ** 2 + 2)
    pressure = (g + 1) / (2 * g * mach_n ** 2 - (g - 1))
    return density ** (g / (g - 1)) * pressure ** (1 / (g - 1))


def mach_after_normal_shock(mach, g=GAMMA_AIR):
    return sqrt(((g - 1) * mach ** 2 + 2) / (2 * g * mach ** 2 - (g - 1)))


def area_ratio(mach, g=GAMMA_AIR):
    """Isentropic A/A*."""
    return ((2 / (g + 1)) * total_temperature(mach, g)) ** ((g + 1) / (2 * (g - 1))) / mach


def subsonic_mach(ratio, g=GAMMA_AIR):
    return brentq(lambda mach: area_ratio(mach, g) - ratio, 1e-4, 1.0)


def cone_flow(mach, shock_deg, g=GAMMA_AIR):
    """Taylor-Maccoll flow behind a conical shock: (cone half-angle deg, surface Mach, Mach behind shock)."""
    beta = radians(shock_deg)
    normal = mach * sin(beta)
    turn = atan(2 / tan(beta) * (normal ** 2 - 1) / (mach ** 2 * (g + cos(2 * beta)) + 2))
    mach_2 = mach_after_normal_shock(normal, g) / sin(beta - turn)
    speed = (2 / ((g - 1) * mach_2 ** 2) + 1) ** -0.5      # V / V_max

    def rhs(theta, v):
        radial, tangential = v
        a = (g - 1) / 2 * (1 - radial ** 2 - tangential ** 2)
        return [tangential, (radial * tangential ** 2 - a * (2 * radial + tangential / tan(theta)))
                / (a - tangential ** 2)]

    surface = lambda theta, v: v[1]
    surface.terminal, surface.direction = True, 1
    flow = solve_ivp(rhs, [beta, 1e-6], [speed * cos(beta - turn), -speed * sin(beta - turn)],
                     events=surface, rtol=1e-9, atol=1e-11)
    if not flow.t_events[0].size:
        return 0.0, mach_2, mach_2
    v_cone = flow.y_events[0][0][0]
    return degrees(flow.t_events[0][0]), sqrt(2 / ((g - 1) * (v_cone ** -2 - 1))), mach_2


@lru_cache
def cone_shock(mach, half_angle=CONE_HALF_ANGLE):
    """Weak attached conical shock: (shock angle deg, surface Mach, Mach behind shock), or None if detached."""
    mach_angle = degrees(np.arcsin(1 / mach))
    if mach_angle > 85:
        return None
    steepest = minimize_scalar(lambda b: -cone_flow(mach, b)[0], bounds=(mach_angle + 1e-3, 89.9),
                               method="bounded", options={"xatol": 1e-4}).x
    if cone_flow(mach, steepest)[0] < half_angle:
        return None
    shock = brentq(lambda b: cone_flow(mach, b)[0] - half_angle, mach_angle + 1e-3, steepest, xtol=1e-9)
    return (shock, *cone_flow(mach, shock)[1:])


def spike_inlet_recovery(mach):
    """Conical shock followed by a normal shock at the Mach number just behind it."""
    cone = cone_shock(mach)
    if cone is None:
        return None
    shock, _, mach_2 = cone
    return shock_recovery(mach * sin(radians(shock))) * shock_recovery(mach_2)


# --- geometry from the model source (inches, stations from the inlet lip) ----------------------

def duct(model, x):
    """Shell inside radius and inner-body radius at stations x."""
    shell = np.interp(x, *zip(*model.SHELL_ID, (model.X_NOZ, 8.0), (model.X_EXIT, model.R_EXIT)))
    spike = np.interp(x - model.SPIKE_TIP, *zip(*model.SPIKE))
    body = np.where(x < model.CENTREBODY[0][0], spike, np.interp(x, *zip(*model.CENTREBODY)))
    return shell, np.where(x > model.CENTREBODY[-1][0], 0.0, body)


def flow_area(model, x):
    shell, body = duct(model, np.asarray(x, dtype=float))
    return pi * (shell ** 2 - body ** 2)


def station_rows(model, chamber_area):
    stations = [("Inlet lip", 0.0), ("Shell reaches chamber diameter", model.SHELL_ID[-1][0]),
                ("Fuel injector", model.X_INJ), ("Centre-body end", model.CENTREBODY[-1][0]),
                ("Combustion chamber", model.X_FH), ("Nozzle exit, plug clear", model.X_EXIT)]
    rows = []
    for label, station in stations:
        shell, body = (float(v) for v in duct(model, np.array(station)))
        area = pi * (shell ** 2 - body ** 2)
        rows.append({"label": label, "x_mm": station * IN, "shell_mm": shell * IN, "body_mm": body * IN,
                     "area_cm2": area * IN ** 2 / 100, "ratio": area / chamber_area})
    return rows


# --- figures ----------------------------------------------------------------------------------

def figure_duct(model, path):
    x = np.linspace(model.SPIKE_TIP, model.X_EXIT, 1500)
    inside = x >= 0
    shell, body = duct(model, x)
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(FIGURE_WIDTH, 3.4), sharex=True, height_ratios=[1, 1.2])
    top.fill_between(x * IN, body * IN, facecolor=LIGHT, edgecolor=INK, linewidth=0.8)
    top.plot(x[inside] * IN, shell[inside] * IN)
    top.annotate("shell, $r_s$", (2900, 203.2), xytext=(0, 5), textcoords="offset points", ha="center")
    top.annotate("inner body, $r_b$", (1150, 30), ha="center")
    top.set(ylabel="$r$, mm", ylim=(0, 280))
    bottom.plot(x[inside] * IN, flow_area(model, x[inside]) * IN ** 2 / 100)
    for name, station in (("injector", model.X_INJ), ("flame holder", model.X_FH), ("nozzle", model.X_NOZ)):
        for axis in (top, bottom):
            axis.axvline(station * IN, color=GREY, linewidth=0.5, linestyle=":")
        bottom.annotate(name, (station * IN, 70), xytext=(3, 0), textcoords="offset points", fontsize=8,
                        rotation=90, va="bottom")
    bottom.set(xlabel="$x$, mm", ylabel="$A$, cm$^2$", ylim=(0, 1500))
    for axis, tag in ((top, "(a)"), (bottom, "(b)")):
        axis.text(0.015, 0.9, tag, transform=axis.transAxes, va="top")
    return save_figure(fig, path)


def figure_recovery(conditions, path):
    mach = np.linspace(1.0, 2.2, 61)
    spike = np.array([spike_inlet_recovery(m) or np.nan for m in mach])
    fig, axis = plt.subplots(figsize=(FIGURE_WIDTH, 2.9))
    axis.plot(mach, spike, label=f"${CONE_HALF_ANGLE:.0f}^\\circ$ cone shock and normal shock")
    axis.plot(mach, [shock_recovery(m) for m in mach], linestyle="--", label="Normal shock alone")
    axis.plot(mach, 1 - 0.075 * (mach - 1) ** 1.35, linestyle="-.", linewidth=0.8, label="MIL-E-5008B")
    for row in conditions:
        axis.plot(row["mach"], row["spike"], "o", markerfacecolor="white", zorder=3)
        axis.annotate(f"$M_\\infty = {row['mach']:.2f}$", (row["mach"], row["spike"]), xytext=(0, 7),
                      textcoords="offset points", ha="center", fontsize=9)
    axis.set(xlabel="$M_\\infty$", ylabel="$\\eta$", xlim=(1.0, 2.2), ylim=(0.6, 1.04))
    axis.legend(loc="lower left")
    return save_figure(fig, path)


def figure_plug(plug_rows, path):
    fraction = np.linspace(0.40, 0.90, 101)
    fig, axis = plt.subplots(figsize=(FIGURE_WIDTH, 2.6))
    axis.axvspan(*PLUG_AREA, color=LIGHT, linewidth=0)
    for g, dashes in ((GAMMA_HOT, "-"), (GAMMA_AIR, "--")):
        axis.plot(fraction, [subsonic_mach(1 / f, g) for f in fraction], linestyle=dashes,
                  label=f"$\\gamma = {g}$")
    axis.plot([row["fraction"] for row in plug_rows], [row["mach"] for row in plug_rows], "o",
              markerfacecolor="white", zorder=3)
    axis.set(xlabel="$A_e/A_c$", ylabel="$M_c$", xlim=(0.40, 0.90), ylim=(0.2, 0.7))
    axis.legend(loc="upper left")
    return save_figure(fig, path)


def cad_image(cfg, step, work):
    """Exterior render of the saved STEP, cropped to the engine; reused while newer than the STEP."""
    from PIL import Image
    view = cfg["renders"][0]
    source, target = work / (view["id"] + ".png"), work / "cad_exterior.png"
    if not source.is_file() or source.stat().st_mtime < step.stat().st_mtime:
        render_views({"renders": [view]}, step, work)
    with Image.open(source) as image:
        width, height = image.size
        image.crop((0, int(height * 0.30), width, int(height * 0.71))).save(target)
    return target


# --- report -----------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tex-only", action="store_true", help="Write the .tex and figures without compiling")
    parser.add_argument("--no-render", action="store_true", help="Leave out the CAD render")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = load_config(MANIFEST, require_step=False)
    source, step = (ROOT / cfg["model"][key] for key in ("source", "step"))
    model = load_model(source)
    work = ROOT / "tmp" / "latex" / source.stem
    work.mkdir(parents=True, exist_ok=True)
    plot_style()

    chamber_area = pi * 8.0 ** 2
    capture_area = pi * model.SHELL_ID[0][1] ** 2
    stations = station_rows(model, chamber_area)
    conditions = []
    for mach, projection in FREE_JET_MACH.items():
        shock, surface_mach, mach_2 = cone_shock(mach)
        conditions.append({
            "mach": mach, "t_ratio": total_temperature(mach), "p_ratio": total_pressure(mach),
            "shock": shock, "lip": degrees(atan(model.SHELL_ID[0][1] / projection)), "projection_mm": projection * IN,
            "surface_mach": surface_mach, "mach_2": mach_2, "normal": shock_recovery(mach),
            "spike": spike_inlet_recovery(mach), "mil": 1 - 0.075 * (mach - 1) ** 1.35})
    plug = [{"fraction": f, "ratio": 1 / f, "mach": subsonic_mach(1 / f, GAMMA_HOT),
             "mach_air": subsonic_mach(1 / f, GAMMA_AIR)} for f in (PLUG_AREA[0], 0.60, 0.70, PLUG_AREA[1])]

    figure_duct(model, work / "duct.pdf")
    figure_recovery(conditions, work / "recovery.pdf")
    figure_plug(plug, work / "plug.pdf")
    render = None if args.no_render or not step.is_file() else cad_image(cfg, step, work).name

    design = conditions[-1]
    context = {
        "title": cfg["title"], "subtitle": "Flow-path areas and ideal inlet and exit estimates",
        "document_id": cfg["document_id"] + "-FP", "revision": cfg.get("revision", "A"),
        "date": f"{date.today().day} {date.today():%B %Y}", "render": render,
        "references": cfg.get("sources", []) + METHOD_REFERENCES,
        "source_hash": digest(source)[:16], "source_path": cfg["model"]["source"],
        "gamma_air": GAMMA_AIR, "gamma_hot": GAMMA_HOT, "cone": CONE_HALF_ANGLE,
        "stations": stations, "conditions": conditions, "plug": plug, "design": design,
        "capture_cm2": capture_area * IN ** 2 / 100, "chamber_cm2": chamber_area * IN ** 2 / 100,
        "exit_fraction": (model.R_EXIT / 8.0) ** 2, "plug_area": PLUG_AREA,
        "lip_gap": max(abs(row["shock"] - row["lip"]) for row in conditions),
        "gamma_gap": max(abs(row["mach"] - row["mach_air"]) for row in plug),
        "diffuser_ratio": stations[1]["area_cm2"] / stations[0]["area_cm2"],
    }
    output = args.output.resolve() if args.output else ROOT / "output" / "pdf" / (source.stem + "_flow_path.pdf")
    build("naca_lewis_16in_ramjet.tex", context, output, work, compile_pdf=not args.tex_only)


if __name__ == "__main__":
    main()

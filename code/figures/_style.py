"""Shared matplotlib style for all paper figures.

Import and call :func:`apply` at the top of every ``fig_*.py`` script so figures
are visually consistent. Keep this file free of data logic.
"""

from __future__ import annotations

import matplotlib as mpl

# Colour-blind-safe categorical palette (Okabe-Ito).
PALETTE = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # green
    "#D55E00",  # vermilion
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
]

# Sequential ramp for continuous rasters; diverging ramp for change / residual maps.
SEQUENTIAL_CMAP = "cividis"
DIVERGING_CMAP = "RdBu_r"

RC_PARAMS: dict[str, object] = {
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.6,
    "axes.grid": False,
    "axes.prop_cycle": mpl.cycler(color=PALETTE),
    "lines.linewidth": 1.0,
    "pdf.fonttype": 42,  # editable text in Illustrator / InDesign
    "ps.fonttype": 42,
    "svg.fonttype": "none",
}

# Single- and double-column widths for a typical journal (inches).
WIDTH_1COL = 3.5
WIDTH_2COL = 7.2


def apply() -> None:
    """Apply the project rcParams to the active matplotlib session."""
    mpl.rcParams.update(RC_PARAMS)


def savefig(fig, out_dir, stem: str) -> list[str]:
    """Save ``fig`` as vector PDF + SVG and a 300 dpi PNG under ``out_dir``.

    Returns the written paths. Writing the provenance sidecar is the caller's job.
    """
    from pathlib import Path

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for ext in ("pdf", "svg", "png"):
        path = out / f"{stem}.{ext}"
        fig.savefig(path)
        written.append(str(path))
    return written

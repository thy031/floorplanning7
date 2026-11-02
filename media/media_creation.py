#!/usr/bin/env python3
"""Dark-theme SA floorplan slides + animated MP4.

Uses:
  TTSOL-en-US-AvaMultilingual-20261102-122557.mp3  (short pitch ~2:38)
  TTSOL-en-US-AvaMultilingual-20261102-120545.mp3  (full lecture ~4:46)
  transcript-sa-en.md  (scene outline)
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from moviepy import AudioFileClip, ImageClip, ImageSequenceClip, concatenate_videoclips
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / "_anim_frames"
TTS_SHORT = ROOT / "TTSOL-en-US-AvaMultilingual-20261102-122557.mp3"
TTS_FULL = ROOT / "TTSOL-en-US-AvaMultilingual-20261102-120545.mp3"
OUT_MP4 = ROOT / "simulated_annealing_floorplan.mp4"
OUT_PDF = ROOT / "simulated_annealing_floorplan.pdf"

BG = "#0F172A"
CARD = "#1E293B"
INK = "#F8FAFC"
MUTED = "#CBD5E1"
TEAL = "#0D9488"
RED = "#EF4444"
GREEN = "#22C55E"
SKY = "#38BDF8"
SLATE = "#64748B"

COLOR_MAP = {
    "A": "#0D9488",
    "B": "#EA580C",
    "C": "#0284C7",
    "D": "#8B5CF6",
    "E": "#EAB308",
}

# Lab-07 toy instance (10×8 outline)
BAD = {
    "A": (0, 0, 3, 2),
    "B": (3, 0, 2, 3),
    "C": (5, 0, 2, 2),
    "D": (0, 2, 3, 1),
    "E": (9, 0, 2, 2),
}
GOLDEN = {
    "A": (0, 0, 3, 2),
    "B": (3, 0, 2, 3),
    "C": (5, 0, 2, 2),
    "D": (0, 2, 3, 1),
    "E": (7, 0, 2, 2),
}

# Coordinates from the original media_creation.py (PDF comparison)
BAD_PDF = {
    "A": (0, 0, 4, 3),
    "B": (3, 0, 4, 9),
    "C": (6, 0, 3, 3),
    "D": (0, 3, 3, 3),
    "E": (8, 0, 3, 4),
}
GOLDEN_PDF = {
    "A": (0, 0, 4, 3),
    "B": (4, 0, 4, 3),
    "C": (0, 3, 4, 4),
    "D": (4, 3, 3, 4),
    "E": (7, 3, 3, 4),
}


def _fig():
    fig, ax = plt.subplots(figsize=(12.80, 7.20), dpi=100, facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_position([0.06, 0.10, 0.88, 0.72])
    return fig, ax


def _header(fig, badge: str, title: str, subtitle: str = ""):
    fig.text(0.06, 0.93, badge.upper(), color=TEAL, fontsize=11, fontweight="bold", ha="left")
    fig.text(0.06, 0.875, title, color=INK, fontsize=22, fontweight="bold", ha="left")
    if subtitle:
        fig.text(0.06, 0.825, subtitle, color=MUTED, fontsize=13, ha="left")
    fig.patches.append(
        FancyBboxPatch(
            (0, 7.16),
            12.80,
            0.06,
            boxstyle="square,pad=0",
            facecolor=TEAL,
            edgecolor="none",
            transform=fig.dpi_scale_trans,
            figure=fig,
        )
    )


def _save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)


def draw_floorplan(ax, modules, e_x=None, show_pocket=False, xmax=12, ymax=10):
    chip = patches.Rectangle(
        (0, 0), 10, 8, linewidth=2, edgecolor=SLATE, facecolor="none", linestyle="--"
    )
    ax.add_patch(chip)
    if show_pocket:
        pocket = patches.Rectangle(
            (7, 0), 2, 2, linewidth=1.5, edgecolor=TEAL, facecolor="none", linestyle=":"
        )
        ax.add_patch(pocket)
        ax.text(8, 1, "pocket", color=TEAL, fontsize=9, ha="center", va="center")
    spill = patches.Rectangle((10, 0), 2.2, 8, linewidth=0, facecolor="#7F1D1D", alpha=0.25)
    ax.add_patch(spill)
    ax.text(11.1, 7.4, "out", color=RED, fontsize=9, ha="center")
    for mid, (x, y, w, h) in modules.items():
        if mid == "E" and e_x is not None:
            x = e_x
        rect = patches.Rectangle(
            (x, y), w, h, linewidth=1.5, edgecolor=INK, facecolor=COLOR_MAP[mid], alpha=0.9
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, mid, color="#FFFFFF", weight="bold", fontsize=14, ha="center", va="center")
        if mid == "E" and x + w > 10.01:
            ax.text(x + w / 2, y + h + 0.35, "spills!", color=RED, fontsize=10, ha="center", fontweight="bold")
    ax.set_xlim(-0.6, xmax)
    ax.set_ylim(-1.2, ymax)
    ax.set_aspect("equal")
    ax.axis("off")


def render_floorplan_frame(modules, title, subtitle, filename, cost_text, is_legal, e_x=None, pocket=False):
    """Kept for PDF generation (4.5×6 card)."""
    fig, ax = plt.subplots(figsize=(6, 4.5), facecolor=BG)
    ax.set_facecolor(BG)
    draw_floorplan(ax, modules, e_x=e_x, show_pocket=pocket, xmax=12, ymax=10)
    plt.suptitle(title, color=INK, fontsize=13, fontweight="bold", x=0.08, y=0.96, ha="left")
    plt.title(subtitle, color=TEAL, fontsize=10, x=0.08, y=0.90, ha="left")
    badge_color = GREEN if is_legal else RED
    ax.text(
        0.2,
        -0.7,
        cost_text,
        color=badge_color,
        fontsize=11,
        weight="bold",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.35", facecolor=CARD, edgecolor=badge_color),
    )
    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches="tight", facecolor=BG)
    plt.close()


def slide_title(path: Path, badge: str, title: str, lines: list[str]):
    fig, ax = plt.subplots(figsize=(12.80, 7.20), dpi=100, facecolor=BG)
    ax.axis("off")
    fig.text(0.08, 0.72, badge.upper(), color=TEAL, fontsize=13, fontweight="bold")
    fig.text(0.08, 0.58, title, color=INK, fontsize=32, fontweight="bold")
    y = 0.46
    for line in lines:
        fig.text(0.08, y, line, color=MUTED, fontsize=16)
        y -= 0.07
    fig.text(0.08, 0.10, "learn_floorplanning  ·  Lab 07 simulated annealing", color=SLATE, fontsize=12)
    _save(fig, path)


def slide_floorplan(path: Path, badge, title, subtitle, modules, cost, legal, e_x=None, pocket=False):
    fig, ax = _fig()
    fig.text(0.06, 0.93, badge.upper(), color=TEAL, fontsize=11, fontweight="bold")
    fig.text(0.06, 0.875, title, color=INK, fontsize=22, fontweight="bold")
    fig.text(0.06, 0.825, subtitle, color=MUTED, fontsize=13)
    draw_floorplan(ax, modules, e_x=e_x, show_pocket=pocket)
    badge_color = GREEN if legal else RED
    ax.text(
        0.1,
        -0.7,
        cost,
        color=badge_color,
        fontsize=13,
        weight="bold",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=CARD, edgecolor=badge_color),
    )
    _save(fig, path)


def slide_split(path: Path, badge, title):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.80, 7.20), dpi=100, facecolor=BG)
    for ax in (ax1, ax2):
        ax.set_facecolor(BG)
    fig.text(0.06, 0.93, badge.upper(), color=TEAL, fontsize=11, fontweight="bold")
    fig.text(0.06, 0.875, title, color=INK, fontsize=22, fontweight="bold")
    draw_floorplan(ax1, BAD, show_pocket=True)
    ax1.set_title("Bad seed   cost 1,044   illegal", color=RED, fontsize=12, pad=8)
    draw_floorplan(ax2, GOLDEN)
    ax2.set_title("Golden   cost 36   legal", color=GREEN, fontsize=12, pad=8)
    plt.tight_layout(rect=(0.03, 0.04, 0.97, 0.80))
    _save(fig, path)


def slide_bullets(path: Path, badge, title, bullets: list[str]):
    fig, ax = plt.subplots(figsize=(12.80, 7.20), dpi=100, facecolor=BG)
    ax.axis("off")
    fig.text(0.06, 0.93, badge.upper(), color=TEAL, fontsize=11, fontweight="bold")
    fig.text(0.06, 0.86, title, color=INK, fontsize=24, fontweight="bold")
    y = 0.74
    for b in bullets:
        fig.patches.append(
            plt.Circle((0.075, y + 0.012), 0.008, transform=fig.transFigure, color=TEAL)
        )
        fig.text(0.10, y, b, color=MUTED, fontsize=16, va="center")
        y -= 0.10
    _save(fig, path)


def slide_code(path: Path, badge, title, lines: list[str]):
    fig, ax = plt.subplots(figsize=(12.80, 7.20), dpi=100, facecolor=BG)
    ax.axis("off")
    fig.text(0.06, 0.93, badge.upper(), color=TEAL, fontsize=11, fontweight="bold")
    fig.text(0.06, 0.86, title, color=INK, fontsize=24, fontweight="bold")
    box = FancyBboxPatch(
        (0.06, 0.12),
        0.88,
        0.68,
        boxstyle="round,pad=0.02,rounding_size=0.01",
        transform=fig.transFigure,
        facecolor=CARD,
        edgecolor="#334155",
        linewidth=1,
    )
    fig.add_artist(box)
    y = 0.72
    for line in lines:
        fig.text(0.09, y, line, color=SKY, fontsize=14, fontfamily="monospace")
        y -= 0.055
    _save(fig, path)


def write_slide_sequence(dest: Path, n: int, renderer) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        u = i / max(n - 1, 1)
        ease = 1 - (1 - u) ** 2
        renderer(i, ease).savefig(dest / f"f{i:04d}.png", dpi=100, facecolor=BG)
        plt.close("all")


def anim_e_home(dest: Path, seconds: float, fps: int = 24) -> Path:
    n = max(int(seconds * fps), 24)

    def one(_i, ease):
        ex = 9 + (7 - 9) * ease
        legal = ex <= 7.05
        fig, ax = _fig()
        fig.text(0.06, 0.93, "IMPROVE STEP", color=TEAL, fontsize=11, fontweight="bold")
        fig.text(0.06, 0.875, "Slide E into the empty pocket", color=INK, fontsize=22, fontweight="bold")
        fig.text(0.06, 0.825, "Cost falls below 1,000 · legality flips to true", color=MUTED, fontsize=13)
        pack = dict(BAD)
        draw_floorplan(ax, pack, e_x=ex, show_pocket=ex > 7.05)
        cost = "Cost 36  ·  legal" if legal else "Cost 1,044  ·  illegal"
        ax.text(
            0.1,
            -0.7,
            cost,
            color=GREEN if legal else RED,
            fontsize=13,
            weight="bold",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=CARD, edgecolor=GREEN if legal else RED),
        )
        return fig

    write_slide_sequence(dest, n, one)
    return dest


# ----------------------------------------------------------------------
# PDF (reportlab) — kept from original media_creation.py
# ----------------------------------------------------------------------
def generate_pdf_slides(output_pdf=None):
    output_pdf = str(output_pdf or OUT_PDF)
    frame_bad = ROOT / "frame_bad.png"
    frame_golden = ROOT / "frame_golden.png"
    render_floorplan_frame(
        BAD,
        "Step 1: Bad Overflow Seed",
        "Illegal placement incurs penalty tax",
        str(frame_bad),
        "Cost: ~1044 | Legality: False",
        False,
        pocket=True,
    )
    render_floorplan_frame(
        GOLDEN,
        "Step 2: Golden Legal Packing",
        "Zero overlap; cost drops below penalty floor",
        str(frame_golden),
        "Cost: ~36 | Legality: True",
        True,
    )

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=(720, 405),
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=20,
    )
    title_style = ParagraphStyle(
        "T", fontName="Helvetica-Bold", fontSize=24, textColor=colors.HexColor(INK), leading=28, spaceAfter=8
    )
    badge_style = ParagraphStyle(
        "B", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor(TEAL), spaceAfter=4
    )
    body_style = ParagraphStyle(
        "C", fontName="Helvetica", fontSize=10, textColor=colors.HexColor(MUTED), leading=14
    )
    code_style = ParagraphStyle(
        "CD", fontName="Courier", fontSize=9.5, textColor=colors.HexColor(SKY), leading=13
    )
    elements = []

    def draw_bg(canvas, doc_):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(BG))
        canvas.rect(0, 0, doc_.pagesize[0], doc_.pagesize[1], fill=True, stroke=False)
        canvas.setFillColor(colors.HexColor(TEAL))
        canvas.rect(0, doc_.pagesize[1] - 4, doc_.pagesize[0], 4, fill=True, stroke=False)
        canvas.restoreState()

    elements.append(Spacer(1, 40))
    elements.append(Paragraph("FLOORPLANNING FOR EDA • LAB 07", badge_style))
    elements.append(Paragraph("Simulated Annealing Floorplan Search", title_style))
    elements.append(Paragraph("Toy cost adds one thousand when a packing is illegal", body_style))
    elements.append(Spacer(1, 40))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#334155"), spaceAfter=15))
    elements.append(Paragraph("learn_floorplanning — 07 simulated annealing fp", body_style))
    elements.append(PageBreak())

    elements.append(Paragraph("ALGORITHM SPECIFICATION", badge_style))
    elements.append(Paragraph("Pseudocode Workflow", title_style))
    code_text = (
        "INPUT: Modules, Temp T_0, Cooling Rate alpha<br/>"
        "cost = deadspace + HPWL + 1000 * (!legal)<br/><br/>"
        "WHILE T &gt; T_min DO:<br/>"
        "&nbsp;&nbsp;S_cand = saSwap(S_curr) &nbsp;// Swap origin coordinates<br/>"
        "&nbsp;&nbsp;delta_C = cost(S_cand) - cost(S_curr)<br/>"
        "&nbsp;&nbsp;IF delta_C &lt;= 0 OR rand() &lt; e<super>(-delta_C/T)</super>:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;S_curr = S_cand<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;IF legal(S_curr) AND cost(S_curr) &lt; cost(S_best):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;S_best = S_curr<br/>"
        "&nbsp;&nbsp;T = T * alpha"
    )
    elements.append(
        Table(
            [[Paragraph(code_text, code_style)]],
            colWidths=[672],
            style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(CARD)), ("PADDING", (0, 0), (-1, -1), 12)],
        )
    )
    elements.append(PageBreak())

    elements.append(Paragraph("TRY THESE", badge_style))
    elements.append(Paragraph("Algorithm sketch", title_style))
    sketch_text = (
        "INPUT: pack / representation, T schedule<br/>"
        "OUTPUT: best legal low-cost pack<br/>"
        "cost ← 1000·¬legal + deadspace + α·HPWL<br/>"
        "propose neighbor (swap/move/perturb)<br/>"
        "accept if Δ&lt;0 or rand &lt; e^(−Δ/T)<br/>"
        "keep best; cool T<br/>"
        "GOLDEN legal cost≈36; bad≈1044"
    )
    elements.append(
        Table(
            [[Paragraph(sketch_text, code_style)]],
            colWidths=[672],
            style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(CARD)), ("PADDING", (0, 0), (-1, -1), 12)],
        )
    )
    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph(
            "Try: (1) start from the overflow seed and read cost ≈ 1044. "
            "(2) saSwap E into the empty pocket — legality true, cost ≈ 36. "
            "(3) worsening moves only with e^(−ΔC/T); rescore after every swap; do not quench.",
            body_style,
        )
    )
    elements.append(PageBreak())

    elements.append(Paragraph("STATE TRANSITION", badge_style))
    elements.append(Paragraph("Bad Seed vs. Golden Packing", title_style))
    img1 = RLImage(str(frame_bad), width=320, height=240)
    img2 = RLImage(str(frame_golden), width=320, height=240)
    comp_table = Table([[img1, img2]], colWidths=[336, 336])
    comp_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    elements.append(comp_table)
    elements.append(PageBreak())

    elements.append(Paragraph("DEBUGGING & CHECKLIST", badge_style))
    elements.append(Paragraph("Implementation Pitfalls", title_style))
    pitfalls_text = (
        "• <b>Accepting illegal states without penalty:</b> Leaves solver stuck in invalid layouts.<br/>"
        "• <b>Forgetting to rescore:</b> Evaluating Metropolis state with stale costs.<br/>"
        "• <b>Quenching (Cooling too fast):</b> Traps search in local minima prematurely.<br/>"
        "• <b>Missing the empty-pocket move:</b> Pairwise swaps cannot fill the hole."
    )
    elements.append(
        Table(
            [[Paragraph(pitfalls_text, body_style)]],
            colWidths=[672],
            style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(CARD)), ("PADDING", (0, 0), (-1, -1), 14)],
        )
    )
    doc.build(elements, onFirstPage=draw_bg, onLaterPages=draw_bg)
    print(f"Presentation generated successfully: {output_pdf}")


# ----------------------------------------------------------------------
# Animated MP4 — Ava TTS + transcript scenes
# ----------------------------------------------------------------------
def _still(path: Path, duration: float) -> ImageClip:
    return ImageClip(str(path)).with_duration(duration)


def generate_mp4_animation(output_mp4=None):
    output_mp4 = Path(output_mp4 or OUT_MP4)
    FRAMES.mkdir(parents=True, exist_ok=True)
    fps = 24

    short = AudioFileClip(str(TTS_SHORT))
    full = AudioFileClip(str(TTS_FULL))
    d_short, d_full = float(short.duration), float(full.duration)

    # --- Part 1: short pitch (122557), timestamps from Whisper ---
    p1 = FRAMES / "p1"
    p1.mkdir(exist_ok=True)
    slide_title(
        p1 / "cover.png",
        "Floorplanning for EDA · Lab 07",
        "Simulated Annealing\nFloorplan Search",
        [
            "How do you pack blocks inside a tight chip without chaos?",
            "Illegal layouts pay a 1,000-point penalty tax.",
        ],
    )
    slide_floorplan(
        p1 / "modules.png",
        "Toy instance",
        "Modules A–E in a 10×8 outline",
        "Fit every block. No overlap, no spill.",
        GOLDEN,
        "Five blocks · one outline",
        True,
    )
    slide_bullets(
        p1 / "cost.png",
        "Cost model",
        "A 1,000-point penalty tax",
        [
            "cost = deadspace + HPWL + 1000 · (¬legal)",
            "Illegal packing: messy score ≈ 1,044",
            "Golden legal packing: about 36 — no tax",
        ],
    )
    slide_floorplan(
        p1 / "bad.png",
        "Energy landscape",
        "Bad overflow seed",
        "E spills past the right edge",
        BAD,
        "Cost: ~1,044  |  Legality: False",
        False,
        pocket=True,
    )
    slide_floorplan(
        p1 / "golden.png",
        "Energy landscape",
        "Golden legal packing",
        "Deadspace + HPWL only — penalty gone",
        GOLDEN,
        "Cost: ~36  |  Legality: True",
        True,
    )
    slide_code(
        p1 / "metro.png",
        "Execution loop",
        "Metropolis + saSwap",
        [
            "S_cand = saSwap(S_curr)   # swap origin coordinates",
            "delta_C = cost(S_cand) - cost(S_curr)",
            "accept if delta_C <= 0",
            "else if rand() < e^(-delta_C/T)",
            "hot T  →  explore (even messy swaps)",
            "cool T →  keep only tidier layouts",
        ],
    )
    slide_bullets(
        p1 / "cool.png",
        "Cooling schedule",
        "Cost falls; legality flips to true",
        [
            "At high T, worsening moves can still be accepted.",
            "As T cools, cost should drop below 1,000.",
            "That is exactly what a proper schedule prefers.",
        ],
    )
    slide_bullets(
        p1 / "moves.png",
        "Representation",
        "Annealing is only as good as its move set",
        [
            "Coordinate swap is the teaching neighbor.",
            "Pair it with B*-trees or sequence pairs.",
            "Soft module A: reshape 3×2 → 2×3 in the next lab.",
        ],
    )
    slide_bullets(
        p1 / "traps.png",
        "Common traps",
        "Watch these in your implementation",
        [
            "Accepting illegal states without the +1,000 penalty.",
            "Forgetting to rescore immediately after a swap.",
            "Quenching — cooling so fast you never leave the bad seed.",
        ],
    )
    slide_bullets(
        p1 / "turn.png",
        "Your turn",
        "Open simulated-annealing-fp",
        [
            "Demonstrate one improve step: bad → golden.",
            "Match starter metrics, then take the quiz.",
            "Report final packing, cost, and legality.",
        ],
    )

    # Whisper-aligned cuts for 122557
    cuts1 = [
        (0.0, 11.9, p1 / "cover.png"),
        (11.9, 23.4, p1 / "modules.png"),
        (23.4, 33.4, p1 / "cost.png"),
        (33.4, 43.9, p1 / "bad.png"),
        (43.9, 63.3, p1 / "golden.png"),
        (63.3, 89.8, p1 / "metro.png"),
        (89.8, 101.7, p1 / "cool.png"),
        (101.7, 125.9, p1 / "moves.png"),
        (125.9, 144.5, p1 / "traps.png"),
        (144.5, d_short, p1 / "turn.png"),
    ]

    clips = []
    anim1 = FRAMES / "slide_e_short"
    # 91.5–98.6 is “cost falls below 1000” — animate E home there
    for a, b, png in cuts1:
        dur = max(b - a, 0.12)
        if png == p1 / "cool.png":
            anim_e_home(anim1, dur, fps)
            clips.append(ImageSequenceClip(str(anim1), fps=fps).with_duration(dur))
        else:
            clips.append(_still(png, dur))

    # --- Part 2: full lecture (120545) ---
    p2 = FRAMES / "p2"
    p2.mkdir(exist_ok=True)
    slide_title(
        p2 / "hook.png",
        "The referee",
        "Pack the blocks.\nDo not spill.",
        [
            "One overflow or overlap → a 1,000-point fine.",
            "That is simulated annealing floorplan search.",
        ],
    )
    slide_split(p2 / "two.png", "Two benchmark states", "Bad seed 1,044  vs  golden 36")
    slide_code(
        p2 / "formula.png",
        "Cost function",
        "Three terms",
        [
            "cost = C_deadspace + C_HPWL + C_legality",
            "C_legality = 1000  if overlap or spill  else  0",
            "messy:  44 + 1000  =  1,044",
            "tidy:   deadspace + HPWL  ≈  36",
        ],
    )
    slide_code(
        p2 / "pseudo.png",
        "Pseudocode",
        "WHILE T > T_min",
        [
            "S_cand = saSwap(S_curr)",
            "delta_C = cost(S_cand) - cost(S_curr)",
            "IF delta_C <= 0 OR rand() < e^(-delta_C/T):",
            "    S_curr = S_cand",
            "    IF legal and better: S_best = S_curr",
            "T = T * alpha",
        ],
    )
    slide_floorplan(
        p2 / "bad.png",
        "Phase 1",
        "Bad overflow seed",
        "Overlaps / spills trigger the +1,000 tax",
        BAD,
        "Cost ≈ 1,044.4  |  legal = False",
        False,
        pocket=True,
    )
    slide_code(
        p2 / "swap.png",
        "Phase 2",
        "saSwap neighbor",
        [
            "Pick two modules at random.",
            "Exchange lower-left (x, y) origins.",
            "Keep widths and heights fixed.",
            "Accept improving Δ; accept worse Δ with e^(-Δ/T).",
        ],
    )
    slide_floorplan(
        p2 / "golden.png",
        "Phase 3",
        "Golden legal packing",
        "Penalty tax = 0 · cost ≈ 35.7",
        GOLDEN,
        "Cost ≈ 35.7  |  legal = True",
        True,
    )
    slide_bullets(
        p2 / "rep.png",
        "Move set",
        "Pair annealing with a real representation",
        [
            "Origin swaps are the teaching baseline.",
            "B*-tree / sequence pair: zero overlap by construction.",
            "Soft sizing and macros come in the labs that follow.",
        ],
    )
    slide_bullets(
        p2 / "pit.png",
        "Pitfalls",
        "Three traps on the toy instance",
        [
            "No +1,000 penalty → the solver stays illegal.",
            "Stale cost after saSwap → Metropolis is lying.",
            "Quench T too fast → stuck in the bad seed.",
        ],
    )
    slide_bullets(
        p2 / "next.png",
        "Your turn",
        "One improve step, then reshape A",
        [
            "Bad seed → golden packing; cost below 1,000; legal = true.",
            "Next: soft module A from 3×2 to 2×3.",
        ],
    )

    cuts2 = [
        (0.0, 17.0, p2 / "hook.png"),
        (17.0, 47.0, p2 / "two.png"),
        (47.0, 68.6, p2 / "formula.png"),
        (68.6, 102.2, p2 / "pseudo.png"),
        (102.2, 137.2, p2 / "bad.png"),
        (137.2, 200.6, p2 / "swap.png"),
        (200.6, 220.9, "ANIM"),
        (220.9, 244.5, p2 / "rep.png"),
        (244.5, 266.5, p2 / "pit.png"),
        (266.5, d_full, p2 / "next.png"),
    ]
    anim2 = FRAMES / "slide_e_full"
    for a, b, png in cuts2:
        dur = max(b - a, 0.12)
        if png == "ANIM":
            anim_e_home(anim2, dur, fps)
            clips.append(ImageSequenceClip(str(anim2), fps=fps).with_duration(dur))
        else:
            clips.append(_still(png, dur))

    video = concatenate_videoclips(clips, method="compose")
    from moviepy import concatenate_audioclips

    audio = concatenate_audioclips([short, full])
    video = video.with_audio(audio)
    end = min(float(video.duration), float(audio.duration))
    video = video.subclipped(0, end)

    video.write_videofile(
        str(output_mp4),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        bitrate="2500k",
        audio_bitrate="128k",
        logger="bar",
    )
    short.close()
    full.close()
    print(f"Animation MP4 exported successfully: {output_mp4}")
    print(f"duration {end:.1f}s")


if __name__ == "__main__":
    os.chdir(ROOT)
    generate_pdf_slides()
    generate_mp4_animation()

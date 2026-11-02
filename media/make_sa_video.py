#!/usr/bin/env python3
"""Build a Gemini-Notebook-style 16:9 explainer for simulated annealing FP.

Mirrors partitioning_l6/media/spectral-en.mp4: black 1280×720 canvas, vertical
paper card, handwritten captions, then full-width course slides.
"""
from __future__ import annotations

import math
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from gtts import gTTS
from imageio_ffmpeg import get_ffmpeg_exe
from moviepy import AudioFileClip

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "sa-en.mp4"
FRAMES = ROOT / "_sa_frames"
FONTS = ROOT / "fonts"
FFMPEG = get_ffmpeg_exe()

W, H = 1280, 720
PW = 405  # 9:16 strip
PX = (W - PW) // 2
PAPER = (246, 241, 230)
INK = (35, 32, 30)
MUTED = (90, 86, 80)
RED = (176, 48, 48)
TEAL = (15, 107, 92)
GOLD = (176, 137, 0)
WHITE = (255, 253, 248)
CAPTION_BG = (255, 255, 255)

COLORS = {
    "A": (196, 92, 38),
    "B": (42, 111, 106),
    "C": (61, 90, 128),
    "D": (107, 76, 154),
    "E": (176, 137, 0),
}
OUTLINE = (10, 8)
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

SCENES = [
    {
        "id": "hook",
        "caption": "Greedy packing gets stuck",
        "script": "Greedy packing is short-sighted. One block spilling over the edge traps you under a thousand-point penalty.",
        "visual": "scribble",
    },
    {
        "id": "idea",
        "caption": "Annealing explores, then cools",
        "script": "Simulated annealing explores messy swaps while it is hot, then cools toward a legal, low-cost floorplan.",
        "visual": "thermo",
    },
    {
        "id": "modules",
        "caption": "Five blocks, one toy box",
        "script": "Take five modules, A through E, of different sizes, and a ten by eight outline. Fit every block inside. No overlap, no spill.",
        "visual": "pack",
        "pack": "golden",
        "score": None,
    },
    {
        "id": "spill",
        "caption": "E spills outside the box",
        "script": "The bad seed lets block E spill past the right edge. The packing is illegal.",
        "visual": "pack",
        "pack": "bad",
        "score": "1,044",
        "spill": True,
    },
    {
        "id": "penalty",
        "caption": "Illegal packs pay 1,000",
        "script": "Toy cost adds one thousand whenever any block overlaps or sticks out. Gaps are about forty-four. Messy score: one thousand forty-four.",
        "visual": "formula",
    },
    {
        "id": "swap",
        "caption": "A neighbor is a swap",
        "script": "A simple neighbor swaps two modules' lower-left corners and keeps their sizes.",
        "visual": "swap",
    },
    {
        "id": "metropolis",
        "caption": "Accept by Metropolis",
        "script": "Accept the swap if cost drops, or with probability e to the minus delta over T. Hot temperatures allow wild ideas. Cool temperatures keep only tidier moves.",
        "visual": "metro",
    },
    {
        "id": "improve",
        "caption": "Slide E into the pocket",
        "script": "The teaching improve step slides E into the empty pocket. Every block fits. Cost falls to about thirty-six. The penalty vanishes.",
        "visual": "slide",
    },
    {
        "id": "golden",
        "caption": "Golden packing: cost 36",
        "script": "Keep the best legal iterate. Pair annealing with a real move set: polish, B-star, or sequence pair, in the labs that follow.",
        "visual": "pack",
        "pack": "golden",
        "score": "36",
        "win": True,
    },
    {
        "id": "pitfalls",
        "caption": None,
        "script": "Three traps: accepting illegal states without a penalty; forgetting to rescore after a swap; and cooling so fast you never escape the bad seed.",
        "visual": "slide_pitfalls",
    },
    {
        "id": "yourturn",
        "caption": None,
        "script": "Your turn. Open simulated annealing F P. Show the bad seed, then improve to golden. Next: reshape soft module A from three by two to two by three.",
        "visual": "slide_turn",
    },
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = {
        "hand": FONTS / "PatrickHand-Regular.ttf",
        "handb": FONTS / "PatrickHand-Regular.ttf",
        "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "sansb": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    }.get(name)
    if not path or not Path(path).exists():
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(str(path), size)


def paper_base() -> tuple[Image.Image, ImageDraw.Image]:
    img = Image.new("RGB", (W, H), (0, 0, 0))
    paper = Image.new("RGB", (PW, H), PAPER)
    rnd = random.Random(7)
    pix = paper.load()
    for _ in range(1400):
        x, y = rnd.randrange(PW), rnd.randrange(H)
        n = rnd.randint(-8, 8)
        r, g, b = PAPER
        pix[x, y] = (max(0, r + n), max(0, g + n), max(0, b + n))
    img.paste(paper, (PX, 0))
    return img, ImageDraw.Draw(img)


def caption_box(draw: ImageDraw.Image, text: str) -> None:
    f = font("hand", 36)
    max_w = PW - 48
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    line_h = 40
    box_h = 18 + line_h * len(lines)
    box_w = min(max_w + 24, PW - 28)
    x0 = PX + (PW - box_w) // 2
    y0 = H - 28 - box_h
    draw.rounded_rectangle((x0, y0, x0 + box_w, y0 + box_h), 4, fill=CAPTION_BG)
    y = y0 + 8
    for line in lines:
        tw = draw.textlength(line, font=f)
        draw.text((x0 + (box_w - tw) / 2, y), line, font=f, fill=INK)
        y += line_h


def grid_origin() -> tuple[float, float, float]:
    pad = 36
    usable_w = PW - pad * 2
    usable_h = 340
    cell = min(usable_w / OUTLINE[0], usable_h / OUTLINE[1])
    ox = PX + pad + (usable_w - OUTLINE[0] * cell) / 2
    oy = 210
    return ox, oy, cell


def to_xy(ox: float, oy: float, cell: float, x: float, y: float, h: float) -> tuple[float, float]:
    """Lower-left module coords → canvas top-left of rect."""
    return ox + x * cell, oy + (OUTLINE[1] - y - h) * cell


def draw_outline(draw: ImageDraw.Image, ox: float, oy: float, cell: float, spill_zone: bool = False) -> None:
    bw, bh = OUTLINE[0] * cell, OUTLINE[1] * cell
    if spill_zone:
        draw.rectangle((ox + bw, oy, ox + bw + 2.4 * cell, oy + bh), fill=(248, 230, 230))
        f = font("sans", 13)
        draw.text((ox + bw + 8, oy + 8), "outside", font=f, fill=RED)
    draw.rounded_rectangle((ox - 3, oy - 3, ox + bw + 3, oy + bh + 3), 6, outline=INK, width=3, fill=WHITE)
    for i in range(OUTLINE[0] + 1):
        x = ox + i * cell
        draw.line((x, oy, x, oy + bh), fill=(213, 205, 192), width=1)
    for j in range(OUTLINE[1] + 1):
        y = oy + j * cell
        draw.line((ox, y, ox + bw, y), fill=(213, 205, 192), width=1)
    draw.rounded_rectangle((ox - 3, oy - 3, ox + bw + 3, oy + bh + 3), 6, outline=INK, width=3)


def draw_pack(draw: ImageDraw.Image, pack: dict, extra_e_x: float | None = None, pocket: bool = False) -> None:
    ox, oy, cell = grid_origin()
    draw_outline(draw, ox, oy, cell, spill_zone=True)
    if pocket:
        x, y, w, h = 7, 0, 2, 2
        px, py = to_xy(ox, oy, cell, x, y, h)
        draw.rounded_rectangle(
            (px + 4, py + 4, px + w * cell - 4, py + h * cell - 4),
            6,
            outline=TEAL,
            width=2,
        )
        f = font("sans", 14)
        draw.text((px + 8, py + h * cell / 2 - 8), "pocket", font=f, fill=TEAL)
    f = font("sansb", 22)
    for mid, (x, y, w, h) in pack.items():
        if mid == "E" and extra_e_x is not None:
            x = extra_e_x
        cx, cy = to_xy(ox, oy, cell, x, y, h)
        color = COLORS[mid]
        draw.rounded_rectangle(
            (cx + 3, cy + 3, cx + w * cell - 3, cy + h * cell - 3),
            7,
            fill=color,
            outline=WHITE,
            width=2,
        )
        tw = draw.textlength(mid, font=f)
        draw.text((cx + (w * cell - tw) / 2, cy + h * cell / 2 - 14), mid, font=f, fill=WHITE)
        if mid == "E" and x + w > OUTLINE[0] + 0.01:
            sf = font("hand", 22)
            draw.text((cx, cy - 26), "spills!", font=sf, fill=RED)


def score_chip(draw: ImageDraw.Image, score: str, bad: bool) -> None:
    f = font("sansb", 28)
    label = f"cost {score}"
    tw = draw.textlength(label, font=f)
    x0 = PX + (PW - tw - 36) / 2
    y0 = 118
    bg = (248, 230, 230) if bad else (228, 245, 235)
    fg = RED if bad else TEAL
    draw.rounded_rectangle((x0, y0, x0 + tw + 36, y0 + 48), 10, fill=bg)
    draw.text((x0 + 18, y0 + 6), label, font=f, fill=fg)


def title_on_paper(draw: ImageDraw.Image, title: str) -> None:
    f = font("handb", 34)
    tw = draw.textlength(title, font=f)
    draw.text((PX + (PW - tw) / 2, 48), title, font=f, fill=INK)


def render_scribble() -> Image.Image:
    img, draw = paper_base()
    title_on_paper(draw, "the trap")
    rnd = random.Random(3)
    ox, oy = PX + 50, 160
    for i, col in enumerate([(196, 92, 38), (42, 111, 106), (61, 90, 128), (176, 137, 0)]):
        x = ox + rnd.randint(0, 120)
        y = oy + rnd.randint(0, 160)
        w, h = rnd.randint(70, 130), rnd.randint(50, 100)
        draw.rounded_rectangle((x, y, x + w, y + h), 12, fill=col, outline=INK, width=2)
    # box
    draw.rounded_rectangle((PX + 40, 150, PX + PW - 40, 470), 8, outline=INK, width=4)
    draw.line((PX + PW - 70, 300, PX + PW - 10, 250), fill=RED, width=6)
    caption_box(draw, "Greedy packing gets stuck")
    return img


def render_thermo() -> Image.Image:
    img, draw = paper_base()
    title_on_paper(draw, "hot → cool")
    # thermometer
    x = PX + PW // 2
    draw.rounded_rectangle((x - 18, 160, x + 18, 430), 12, outline=INK, width=3, fill=WHITE)
    draw.ellipse((x - 36, 410, x + 36, 482), fill=RED, outline=INK, width=3)
    draw.rectangle((x - 12, 250, x + 12, 430), fill=(220, 90, 60))
    f = font("hand", 28)
    draw.text((x + 36, 170), "cool", font=f, fill=(61, 90, 128))
    draw.text((x + 36, 400), "hot", font=f, fill=RED)
    f2 = font("sans", 18)
    draw.text((PX + 36, 510), "explore  then  keep best", font=f2, fill=MUTED)
    caption_box(draw, "Annealing explores, then cools")
    return img


def render_pack(kind: str, score: str | None, spill: bool = False, win: bool = False, e_x: float | None = None) -> Image.Image:
    img, draw = paper_base()
    title_on_paper(draw, "magic toy box  10×8")
    pack = dict(BAD if kind == "bad" else GOLDEN)
    pocket = kind == "bad"
    draw_pack(draw, pack, extra_e_x=e_x, pocket=pocket)
    if score:
        score_chip(draw, score, bad=(kind == "bad" and not win))
    if win:
        f = font("hand", 26)
        draw.text((PX + 48, 168), "penalty gone", font=f, fill=TEAL)
    cap = {
        "bad": "E spills outside the box",
        "golden": "Five blocks, one toy box" if not win else "Golden packing: cost 36",
    }[kind if not win else "golden"]
    if kind == "bad":
        cap = "E spills outside the box"
    caption_box(draw, cap)
    return img


def render_formula() -> Image.Image:
    img, draw = paper_base()
    title_on_paper(draw, "the points")
    f = font("sansb", 22)
    lines = [
        ("cost = 1000 · ¬legal", INK),
        ("        + gaps + α·HPWL", MUTED),
        ("", INK),
        ("messy  44 + 1000 = 1,044", RED),
        ("tidy   legal → about 36", TEAL),
    ]
    y = 180
    for text, col in lines:
        draw.text((PX + 32, y), text, font=f, fill=col)
        y += 42
    caption_box(draw, "Illegal packs pay 1,000")
    return img


def render_swap() -> Image.Image:
    img, draw = paper_base()
    title_on_paper(draw, "neighbor move")
    ox, oy, cell = grid_origin()
    draw_pack(draw, BAD, pocket=True)
    # arrow between E and pocket
    f = font("hand", 28)
    draw.text((PX + 48, 155), "swap corners, keep sizes", font=f, fill=INK)
    caption_box(draw, "A neighbor is a swap")
    return img


def render_metro() -> Image.Image:
    img, draw = paper_base()
    title_on_paper(draw, "Metropolis")
    f = font("sansb", 20)
    body = [
        "accept if Δ < 0",
        "else if rand < e^(−Δ / T)",
        "",
        "hot T  →  wild swaps OK",
        "cool T →  only tidier",
        "keep best legal iterate",
        "then cool T",
    ]
    y = 160
    for line in body:
        draw.text((PX + 36, y), line, font=f, fill=INK if line else MUTED)
        y += 36
    caption_box(draw, "Accept by Metropolis")
    return img


def render_pitfalls() -> Image.Image:
    img = Image.new("RGB", (W, H), (247, 247, 244))
    draw = ImageDraw.Draw(img)
    for i in range(0, H, 28):
        draw.line((0, i, W, i), fill=(236, 236, 232), width=1)
    draw.text((72, 56), "Pitfalls", font=font("sansb", 48), fill=(28, 36, 33))
    draw.text((72, 118), "Three traps on the toy instance", font=font("sans", 22), fill=MUTED)
    bullets = [
        "Accepting illegal states without a +1,000 penalty.",
        "Forgetting to rescore immediately after a swap.",
        "Cooling so fast you never escape the bad seed.",
        "A frozen robot only swaps occupied seats and never tries the empty pocket.",
    ]
    y = 180
    for b in bullets:
        draw.ellipse((78, y + 10, 90, y + 22), fill=(28, 36, 33))
        draw.text((108, y), b, font=font("sans", 24), fill=(28, 36, 33))
        y += 70
    draw.text((72, H - 48), "learn_floorplanning  —  07 simulated annealing", font=font("sans", 16), fill=MUTED)
    return img


def render_turn() -> Image.Image:
    img = Image.new("RGB", (W, H), (247, 247, 244))
    draw = ImageDraw.Draw(img)
    for i in range(0, H, 28):
        draw.line((0, i, W, i), fill=(236, 236, 232), width=1)
    draw.text((72, 56), "Your turn", font=font("sansb", 48), fill=(28, 36, 33))
    draw.text((72, 118), "Browser lab  ·  implement track", font=font("sans", 22), fill=MUTED)
    bullets = [
        "Open simulated-annealing-fp. Load the bad seed (cost ≥ 1,000).",
        "Improve: slide E home. Cost drops below 1,000; packing is legal.",
        "Assert cost(golden) < cost(bad), and saSwap only exchanges coordinates.",
        "Next lab: reshape soft module A from 3×2 to 2×3.",
    ]
    y = 180
    for b in bullets:
        draw.ellipse((78, y + 10, 90, y + 22), fill=TEAL)
        draw.text((108, y), b, font=font("sans", 24), fill=(28, 36, 33))
        y += 70
    draw.text((72, H - 48), "learn_floorplanning  —  07 simulated annealing", font=font("sans", 16), fill=MUTED)
    return img


def ff(*args: str) -> None:
    r = subprocess.run([FFMPEG, "-y", *args], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2500:])


def tts(text: str, mp3: Path) -> float:
    gTTS(text=text, lang="en", slow=False).save(str(mp3))
    dur = float(AudioFileClip(str(mp3)).duration)
    return dur + 0.35


def still_clip(png: Path, mp3: Path, seconds: float, dest: Path) -> None:
    n = max(int(seconds * 25) + 8, 30)
    ff(
        "-loop", "1",
        "-framerate", "25",
        "-i", str(png),
        "-i", str(mp3),
        "-t", f"{seconds:.3f}",
        "-vf", (
            f"scale=1408:792,"
            f"zoompan=z='min(1.0+0.00055*on,1.06)':d={n}:x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':s=1280x720:fps=25,format=yuv420p"
        ),
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-shortest",
        str(dest),
    )


def anim_clip(frame_dir: Path, mp3: Path, seconds: float, dest: Path) -> None:
    ff(
        "-framerate", "25",
        "-i", str(frame_dir / "f%04d.png"),
        "-i", str(mp3),
        "-t", f"{seconds:.3f}",
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-shortest",
        str(dest),
    )


def write_slide_frames(n: int, dest_dir: Path, renderer) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    n_move = min(n, 40)
    for i in range(n):
        u = min(1.0, i / max(n_move - 1, 1))
        ease = 1 - (1 - u) ** 2
        ex = 9 + (7 - 9) * ease
        img = renderer(ex if i < n_move else 7.0)
        img.save(dest_dir / f"f{i:04d}.png")


def main() -> None:
    FRAMES.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for idx, sc in enumerate(SCENES):
            mp3 = tmp_path / f"n{idx}.mp3"
            print(f"tts {sc['id']} …")
            seconds = tts(sc["script"], mp3)
            n_frames = max(int(seconds * 25), 25)
            clip = tmp_path / f"c{idx}.mp4"
            vis = sc["visual"]
            if vis == "scribble":
                png = FRAMES / f"{sc['id']}.png"
                render_scribble().save(png)
                still_clip(png, mp3, seconds, clip)
            elif vis == "thermo":
                png = FRAMES / f"{sc['id']}.png"
                render_thermo().save(png)
                still_clip(png, mp3, seconds, clip)
            elif vis == "pack":
                png = FRAMES / f"{sc['id']}.png"
                render_pack(
                    sc.get("pack", "golden"),
                    sc.get("score"),
                    spill=sc.get("spill", False),
                    win=sc.get("win", False),
                ).save(png)
                still_clip(png, mp3, seconds, clip)
            elif vis == "formula":
                png = FRAMES / f"{sc['id']}.png"
                render_formula().save(png)
                still_clip(png, mp3, seconds, clip)
            elif vis == "swap":
                png = FRAMES / f"{sc['id']}.png"
                render_swap().save(png)
                still_clip(png, mp3, seconds, clip)
            elif vis == "metro":
                png = FRAMES / f"{sc['id']}.png"
                render_metro().save(png)
                still_clip(png, mp3, seconds, clip)
            elif vis == "slide":
                adir = tmp_path / "slide_frames"
                write_slide_frames(n_frames, adir, lambda ex: render_pack("bad", "1,044" if ex > 7.2 else "36", win=ex <= 7.2, e_x=ex))
                # last frames should show golden score; rewrite caption by using golden pack at end
                last = render_pack("golden", "36", win=True)
                for i in range(max(0, n_frames - 12), n_frames):
                    last.save(adir / f"f{i:04d}.png")
                anim_clip(adir, mp3, seconds, clip)
            elif vis == "slide_pitfalls":
                png = FRAMES / f"{sc['id']}.png"
                render_pitfalls().save(png)
                still_clip(png, mp3, seconds, clip)
            elif vis == "slide_turn":
                png = FRAMES / f"{sc['id']}.png"
                render_turn().save(png)
                still_clip(png, mp3, seconds, clip)
            else:
                raise SystemExit(vis)
            clips.append(clip)
            print(f"  {sc['id']}: {seconds:.1f}s")

        lst = tmp_path / "list.txt"
        lst.write_text("".join(f"file '{c}'\n" for c in clips))
        ff(
            "-f", "concat",
            "-safe", "0",
            "-i", str(lst),
            "-c:v", "libx264",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            str(OUT),
        )
    print("wrote", OUT, "size", OUT.stat().st_size)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build sentence-level WebVTT from transcript-sa-en.md / transcript-sa-zh.md."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "captions"
SITE = (
    ROOT.parent
    / "site"
    / "course-media"
    / "learn_floorplanning"
    / "module03-01-simulated-annealing-fp"
)

SHORT_END = 157.56
FULL_END = 285.65
SHORT_DUR = 157.58  # concat offset for combined mp4

HEADING = {
    "en": (r"## Short clip", r"## Full lecture"),
    "zh": (r"## 短片", r"## 完整课"),
}
TS_RE = re.compile(r"^(\d+):(\d{2})\s+[—–-]\s+.+$")


def ts(sec: float) -> str:
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def tex_to_plain(inner: str) -> str:
    t = inner
    t = re.sub(r"\\mathrm\{([^}]+)\}", r"\1", t)
    t = t.replace("\\Delta", "Δ").replace("\\times", "×").replace("\\,", " ")
    t = re.sub(r"\^\{([^}]+)\}", r"^(\1)", t)
    t = t.replace("{", "").replace("}", "")
    return t.strip()


def clean_caption(text: str) -> str:
    text = re.sub(r"\\\((.+?)\\\)", lambda m: tex_to_plain(m.group(1)), text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_blocks(md: str, heading: str) -> list[tuple[float, str]]:
    m = re.search(heading, md)
    if not m:
        raise SystemExit(f"missing heading {heading}")
    rest = md[m.end() :]
    nxt = re.search(r"^##\s+", rest, re.M)
    if nxt:
        rest = rest[: nxt.start()]
    rest = re.sub(r"```.*?```", "", rest, flags=re.S)
    rest = re.sub(r"^###.*$", "", rest, flags=re.M)
    lines = rest.splitlines()
    blocks: list[tuple[float, str]] = []
    t0: float | None = None
    buf: list[str] = []
    for line in lines:
        raw = line.rstrip()
        hit = TS_RE.match(raw)
        if hit:
            if t0 is not None:
                body = clean_caption(" ".join(buf))
                if body:
                    blocks.append((t0, body))
            t0 = int(hit.group(1)) * 60 + int(hit.group(2))
            buf = []
            continue
        if t0 is None:
            continue
        if raw.strip() in ("---", "***", "___"):
            continue
        if raw.strip():
            buf.append(raw.strip())
    if t0 is not None:
        body = clean_caption(" ".join(buf))
        if body:
            blocks.append((t0, body))
    return blocks


def with_ends(blocks: list[tuple[float, str]], end: float) -> list[tuple[float, float, str]]:
    out = []
    for i, (a, text) in enumerate(blocks):
        b = blocks[i + 1][0] if i + 1 < len(blocks) else end
        out.append((a, b, text))
    return out


def split_en(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) > 110 and ";" in p:
            bits = [b.strip() for b in p.split(";") if b.strip()]
            if bits and not bits[0].endswith((".", "?", "!")):
                bits[0] = bits[0] + ":"
            out.extend(bits)
        else:
            out.append(p)
    return out


def split_zh(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    parts = re.split(r"(?<=[。！？])", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) > 56 and "；" in p:
            out.extend([b.strip() for b in p.split("；") if b.strip()])
        else:
            out.append(p)
    return out


def merge_shortest(parts: list[str], joiner: str) -> list[str]:
    if len(parts) < 2:
        return parts
    lengths = [len(x) for x in parts]
    i = lengths.index(min(lengths))
    if i == 0:
        parts[0] = joiner.join((parts[0], parts[1])).strip()
        del parts[1]
    else:
        parts[i - 1] = joiner.join((parts[i - 1], parts[i])).strip()
        del parts[i]
    return parts


def pair_units(en: str, zh: str) -> list[tuple[str, str]]:
    e = split_en(en)
    z = split_zh(zh)
    while len(e) > len(z) and len(e) > 1:
        e = merge_shortest(e, " ")
    while len(z) > len(e) and len(z) > 1:
        z = merge_shortest(z, "")
    n = max(len(e), len(z), 1)
    while len(e) < n:
        e.append("")
    while len(z) < n:
        z.append("")
    return list(zip(e, z))


def weight(en: str, zh: str) -> int:
    return max(len(en.split()) + max(len(zh), 1) // 2, 1)


def expand(
    timed: list[tuple[float, float, str]],
    zh_timed: list[tuple[float, float, str]],
    offset: float = 0.0,
):
    if len(timed) != len(zh_timed):
        raise SystemExit(f"EN/ZH block count mismatch: {len(timed)} vs {len(zh_timed)}")
    en_cues: list[tuple[float, float, str]] = []
    zh_cues: list[tuple[float, float, str]] = []
    bi_cues: list[tuple[float, float, str]] = []
    for (a0, b0, e), (_, _, z) in zip(timed, zh_timed):
        units = pair_units(e, z)
        weights = [weight(u, v) for u, v in units]
        total = sum(weights) or 1
        span = b0 - a0
        t = a0
        for i, ((u, v), w) in enumerate(zip(units, weights)):
            nxt = b0 if i == len(units) - 1 else t + span * (w / total)
            if nxt - t < 0.9 and i < len(units) - 1:
                nxt = min(b0, t + 0.9)
            a, b = t + offset, nxt + offset
            if u:
                en_cues.append((a, b, u))
            if v:
                zh_cues.append((a, b, v))
            if u or v:
                body = "\n".join(x for x in (u, v) if x)
                bi_cues.append((a, b, body))
            t = nxt
    return en_cues, zh_cues, bi_cues


def write_vtt(path: Path, cues: list[tuple[float, float, str]]) -> None:
    parts = ["WEBVTT\n"]
    for i, (a, b, text) in enumerate(cues, 1):
        body = text.replace("-->", "→").strip()
        parts.append(f"\n{i}\n{ts(a)} --> {ts(b)}\n{body}\n")
    path.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {path.name} ({len(cues)} cues)")


def main() -> None:
    en_md = (ROOT / "transcript-sa-en.md").read_text(encoding="utf-8")
    zh_md = (ROOT / "transcript-sa-zh.md").read_text(encoding="utf-8")
    en_short = with_ends(parse_blocks(en_md, HEADING["en"][0]), SHORT_END)
    zh_short = with_ends(parse_blocks(zh_md, HEADING["zh"][0]), SHORT_END)
    en_full = with_ends(parse_blocks(en_md, HEADING["en"][1]), FULL_END)
    zh_full = with_ends(parse_blocks(zh_md, HEADING["zh"][1]), FULL_END)

    OUT.mkdir(parents=True, exist_ok=True)
    se, sz, sb = expand(en_short, zh_short)
    fe, fz, fb = expand(en_full, zh_full)
    ce, cz, cb = expand(en_short, zh_short)
    fe2, fz2, fb2 = expand(en_full, zh_full, offset=SHORT_DUR)
    ce.extend(fe2)
    cz.extend(fz2)
    cb.extend(fb2)

    files = {
        "sa-short-en.vtt": se,
        "sa-short-zh.vtt": sz,
        "sa-short-bilingual.vtt": sb,
        "sa-full-en.vtt": fe,
        "sa-full-zh.vtt": fz,
        "sa-full-bilingual.vtt": fb,
        "sa-combined-en.vtt": ce,
        "sa-combined-zh.vtt": cz,
        "sa-combined-bilingual.vtt": cb,
    }
    for name, cues in files.items():
        write_vtt(OUT / name, cues)

    if SITE.is_dir():
        for name in (
            "sa-short-en.vtt",
            "sa-short-zh.vtt",
            "sa-short-bilingual.vtt",
            "sa-full-en.vtt",
            "sa-full-zh.vtt",
            "sa-full-bilingual.vtt",
        ):
            shutil.copy2(OUT / name, SITE / name)
            print(f"copied {name} → course-media")


if __name__ == "__main__":
    main()

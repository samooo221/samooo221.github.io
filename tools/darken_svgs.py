#!/usr/bin/env python3
"""Turn the light case-study diagrams into dark ones for the site.

Input:  tools/diagrams-light/<name>.svg (white page, black text, red accent)
Output: diagrams/<name>.svg (page-dark background, light text, grey lines, same red)

What it does, per file:
1. Drops the head block (red bar, big title, subtitle). The HTML section already
   carries the h2 and the lede, so the reader sees one title.
2. Moves the rest up and crops the canvas.
3. Recolours every fill and stroke from the light palette to the dark one.
4. ideas.svg only: replaces the 25 red row dots with red numbers 01-25, matching
   the idea cards on the page.
Run from anywhere: python3 tools/darken_svgs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "diagrams-light"
OUT = ROOT / "diagrams"
NAMES = ["system", "evolution", "timeline", "ideas", "skills", "flow"]

BG = "#111111"      # same as the page background
RED = "#E5262B"
TEXT = {"#111111": "#EDEDED", "#666666": "#B0B0B0", "#9A9A9A": "#8C8C8C", RED: RED}
FILL = {"#111111": "#EDEDED", "#FFFFFF": BG, "#F2F2F2": "#1C1C1C", "#E8E8E8": "#262626",
        "#D6D6D6": "#575757", "#9A9A9A": "#8C8C8C", "#666666": "#B0B0B0",
        "#F6C4C6": "#5A1F21", RED: RED, "none": "none"}
STROKE = {"#111111": "#EDEDED", "#9A9A9A": "#8C8C8C", "#D6D6D6": "#444444",
          "#E8E8E8": "#2E2E2E", "#666666": "#B0B0B0", RED: RED, "none": "none"}
TOP_MARGIN = 28

HEAD_BAR = re.compile(r'<rect x="40\.0" y="34\.0" width="48\.0" height="4\.0"')
HEAD_TITLE = re.compile(r'<text x="40\.0" y="80\.0" font-size="32"')
HEAD_SUB = re.compile(r'<text x="40\.0" y="1[1-9]\d\.0" font-size="18" font-weight="400" fill="#666666"')
BG_RECT = re.compile(r'<rect width="(\d+)" height="(\d+)" fill="#FFFFFF"/>')


def num(attr, line, default=None):
    m = re.search(r'\b' + attr + r'="(-?[\d.]+)"', line)
    return float(m.group(1)) if m else default


def top_of(line):
    """Smallest y an element reaches (rough, good enough to crop a margin)."""
    tag = re.match(r"<(\w+)", line)
    if not tag:
        return None
    t = tag.group(1)
    if t == "rect":
        return num("y", line)
    if t == "circle":
        return num("cy", line) - num("r", line)
    if t == "line":
        return min(num("y1", line), num("y2", line))
    if t == "text":
        return num("y", line) - num("font-size", line) * 0.8
    if t == "path":
        d = re.search(r' d="([^"]+)"', line).group(1)
        # absolute commands only (M, L, H, V, A, Z are all the generator uses)
        ys = []
        for cmd, args in re.findall(r"([MLHVAZ])([^MLHVAZ]*)", d):
            a = [float(x) for x in re.findall(r"-?[\d.]+", args)]
            if cmd in "ML":
                ys += a[1::2]
            elif cmd == "V":
                ys += a
            elif cmd == "A":
                ys += a[6::7]
        return min(ys) if ys else None
    return None


def recolour(line, prev_fill):
    tag = re.match(r"<(\w+)", line).group(1)

    def sub(attr, table):
        def rep(m):
            old = m.group(1)
            if old not in table:
                sys.exit(f"unmapped {attr} {old} in: {line[:120]}")
            return f'{attr}="{table[old]}"'
        return re.sub(attr + r'="([^"]+)"', rep, line)

    if tag == "text":
        m = re.search(r'fill="([^"]+)"', line)
        if m and m.group(1) == "#FFFFFF":
            # white label on a black disc turns dark on the now-light disc; on red it stays white
            new = BG if prev_fill == "#111111" else "#FFFFFF"
            return line.replace('fill="#FFFFFF"', f'fill="{new}"')
        return sub("fill", TEXT)
    line = sub("stroke", STROKE)
    return sub("fill", FILL)


def convert(name):
    lines = (SRC / f"{name}.svg").read_text().splitlines()
    head, body, tail = [], [], []
    w = h = None
    stage = "head"
    for ln in lines:
        if stage == "head":
            m = BG_RECT.match(ln)
            if m:
                w, h = int(m.group(1)), int(m.group(2))
                stage = "body"
                continue
            if ln.startswith("<defs>"):
                ln = re.sub(r'stroke="([^"]+)"', lambda m: f'stroke="{STROKE[m.group(1)]}"', ln)
            head.append(ln)
        elif ln.startswith("</svg>"):
            tail.append(ln)
            stage = "tail"
        elif stage == "body":
            body.append(ln)
    assert w and h, name

    # 1. drop the head block
    kept, dropped, after_title = [], 0, False
    for ln in body:
        if HEAD_BAR.match(ln) or HEAD_TITLE.match(ln) or (after_title and HEAD_SUB.match(ln)):
            after_title = bool(HEAD_TITLE.match(ln)) or after_title
            dropped += 1
            continue
        after_title = False
        kept.append(ln)
    if dropped < 3:
        sys.exit(f"{name}: head block not found (dropped {dropped})")

    # 2. crop the top
    top = min(t for t in (top_of(ln) for ln in kept) if t is not None)
    dy = max(0, int(top) - TOP_MARGIN)
    nh = h - dy

    # 3. recolour
    out_body, prev_fill = [], None
    for ln in kept:
        new = recolour(ln, prev_fill)
        if not ln.startswith("<text"):
            m = re.search(r'fill="([^"]+)"', ln)
            prev_fill = m.group(1) if m else None
        out_body.append(new)

    # 4. ideas: numbered rows
    if name == "ideas":
        n = 0
        numbered = []
        for ln in out_body:
            m = re.match(r'<circle cx="52\.0" cy="([\d.]+)" r="4\.5" fill="#E5262B"', ln)
            if m:
                n += 1
                y = float(m.group(1)) + 5
                numbered.append(f'<text x="40.0" y="{y:.1f}" font-size="15" font-weight="700" '
                                f'fill="{RED}" text-anchor="start">{n:02d}</text>')
            else:
                numbered.append(ln)
        if n != 25:
            sys.exit(f"ideas: expected 25 row dots, found {n}")
        out_body = numbered

    svg_open = head[0]
    svg_open = re.sub(r'height="\d+"', f'height="{nh}"', svg_open, count=1)
    svg_open = re.sub(r'viewBox="0 0 (\d+) \d+"', rf'viewBox="0 0 \1 {nh}"', svg_open)
    out = [svg_open] + head[1:]
    out.append(f'<rect width="{w}" height="{nh}" fill="{BG}"/>')
    out.append(f'<g transform="translate(0,-{dy})">')
    out += out_body
    out.append("</g>")
    out += tail
    (OUT / f"{name}.svg").write_text("\n".join(out) + "\n")
    return w, nh


if __name__ == "__main__":
    for nm in NAMES:
        w, nh = convert(nm)
        print(f"{nm}: {w}x{nh}")

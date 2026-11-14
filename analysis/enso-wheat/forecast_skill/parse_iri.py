# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Read the IRI ENSO forecast archive SVGs (matplotlib) and the official CPC/IRI tables.

- figure4_plot: Nino-3.4 plume per model. Each line is matched to the legend by its style
  (colour, width, dash and marker shape); y in pixels becomes degC through the reference lines
  (0 and +/-0.5); x becomes a season through the nearest tick.
- figure3_plot: IRI probability bars (La Nina / Neutral / El Nino), matched to the legend by
  colour; bar heights are normalized by their sum (the three bars add up to 100%).
- quick look HTML: first table with La Nina / Neutral / El Nino columns (CPC/IRI consensus).

Imported by forecast_skill.py, or run directly: python -I parse_iri.py <svg|html>
"""

from __future__ import annotations

import html as htmlmod
import re
import sys
from pathlib import Path

import numpy as np

NUM = r"-?\d+(?:\.\d+)?"


def _blocks(txt: str, prefix: str, indent: int | None = None) -> list[tuple[str, int, str]]:
    """Blocks <g id="prefixN"> up to the next block of the same prefix. `indent` filters by the
    line indentation (matplotlib indents axis objects by 3 spaces, the legend by 4, ticks by 5)."""
    starts = []
    pat = rf'\n {{{indent}}}<g id="({prefix}\d+)">' if indent else rf'<g id="({prefix}\d+)">'
    for m in re.finditer(pat, txt):
        starts.append((m.group(1), m.start()))
    res = []
    for i, (gid, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(txt)
        res.append((gid, start, txt[start:end]))
    return res


def _comment(s: str) -> str | None:
    m = re.search(r"<!-- (.*?) -->", s)
    return m.group(1).strip() if m else None


def _num(lbl: str) -> float:
    return float(lbl.replace("−", "-"))  # matplotlib writes the minus sign as U+2212


def _axes(txt: str):
    xt = {}
    for _, _, b in _blocks(txt, "xtick_"):
        b = b.split('<g id="ytick_')[0]
        m = re.search(rf'<use xlink:href="#[^"]+" x="({NUM})" y="{NUM}"', b)
        lbl = _comment(b)
        if m and lbl:
            xt[lbl] = float(m.group(1))
    ys, vs = [], []
    for _, _, b in _blocks(txt, "ytick_"):
        m = re.search(rf'<use xlink:href="#[^"]+" x="{NUM}" y="({NUM})"', b)
        lbl = _comment(b)
        if m and lbl:
            try:
                vs.append(_num(lbl))
                ys.append(float(m.group(1)))
            except ValueError:
                pass
    if len(set(ys)) < 2:
        return xt, (float("nan"), float("nan"))
    a, c = np.polyfit(ys, vs, 1)  # value = a*y + c
    return xt, (a, c)


def _marker_defs(txt: str) -> dict[str, str]:
    return {
        m.group(1): re.sub(r"\s+", " ", m.group(2)).strip()
        for m in re.finditer(r'<path id="(m[0-9a-f]+)" d="([^"]*)"', txt)
    }


def _style_key(block: str, mdefs: dict[str, str]) -> tuple | None:
    m = re.search(r'<path d="[^"]*"[^>]*style="([^"]*)"', block)
    if not m:
        return None
    st = dict(kv.split(":", 1) for kv in [x.strip() for x in m.group(1).split(";")] if ":" in kv)
    st = {k.strip(): v.strip() for k, v in st.items()}
    mk = re.search(r'<use xlink:href="#(m[0-9a-f]+)"', block)
    mshape = mdefs.get(mk.group(1), "") if mk else ""
    return (st.get("stroke"), st.get("stroke-width", "1.5"), st.get("stroke-dasharray", ""), mshape)


def _points(block: str) -> list[tuple[float, float]]:
    m = re.search(r'<path d="([^"]*)"', block)
    if not m:
        return []
    return [(float(x), float(y)) for x, y in re.findall(rf"[ML] ({NUM}) ({NUM})", m.group(1))]


def parse_plume(path: Path) -> dict:
    txt = path.read_text(encoding="utf-8", errors="replace")
    title = next((c for c in re.findall(r"<!-- (.*?) -->", txt) if "Predictions of ENSO from" in c), None)
    xt, (a, c) = _axes(txt)
    mdefs = _marker_defs(txt)
    ileg = txt.find('<g id="legend_1">')
    body, leg = txt[:ileg], txt[ileg:]
    # legend: a line2d followed by its text
    legend = []
    for _, _, b in _blocks(leg, "line2d_"):
        k = _style_key(b, mdefs)
        name = _comment(b)
        if k and name is not None:
            legend.append((name.strip(), k))
    # data lines (outside the ticks)
    data = []
    for _, _, b in _blocks(body, "line2d_", indent=3):
        k = _style_key(b, mdefs)
        pts = _points(b)
        if k and len(pts) >= 2:
            data.append((k, pts))
    xs_lbl = sorted(xt.items(), key=lambda kv: kv[1])
    step = np.median(np.diff([x for _, x in xs_lbl])) if len(xs_lbl) > 1 else 1.0

    def season(x: float) -> str | None:
        lbl, xx = min(xs_lbl, key=lambda kv: abs(kv[1] - x))
        return lbl if abs(xx - x) < 0.2 * step else None

    # y-axis calibration: black reference lines (solid = 0; dash-dot = +/-0.5). In some old SVGs the
    # y tick labels come out swapped, so the labels are only a cross-check.
    zero = [
        pts[0][1]
        for kk, pts in data
        if kk[0] == "#000000" and kk[1] == "2" and not kk[2] and abs(pts[0][1] - pts[-1][1]) < 1e-6
    ]
    half = sorted(
        pts[0][1]
        for kk, pts in data
        if kk[0] == "#000000" and kk[1] == "2" and kk[2] and abs(pts[0][1] - pts[-1][1]) < 1e-6
    )
    calibration = "tick_labels"
    a_lbl, c_lbl = a, c
    if len(zero) == 1 and len(half) == 2:
        a = (0.5 - (-0.5)) / (half[0] - half[1])  # half[0] is +0.5 (higher on screen)
        c = -a * zero[0]
        calibration = "reference_lines"
    labels_ok = bool(zero) and abs(a_lbl - a) / abs(a) < 0.02 and abs(a_lbl * zero[0] + c_lbl) < 0.02

    models, ambiguous = {}, []
    used: dict[tuple, int] = {}
    n_leg = {}
    for name, k in legend:
        if name and not name.endswith(":"):
            n_leg[k] = n_leg.get(k, 0) + 1
    for name, k in legend:
        if not name or name.endswith(":"):
            continue
        cand = [pts for kk, pts in data if kk == k]
        j = used.get(k, 0)
        used[k] = j + 1
        if len(cand) != n_leg[k]:
            # repeated style and a line count different from the legend's: cannot tell which is which
            ambiguous.append({"model": name, "lines": len(cand), "in_legend": n_leg[k]})
            continue
        # repeated styles: matplotlib draws in legend order, so the j-th line is the j-th entry
        pts = cand[j]
        models[name] = {season(x): round(a * y + c, 3) for x, y in pts if season(x)}
    return {
        "title": title,
        "models": models,
        "ambiguous": ambiguous,
        "seasons": [lbl for lbl, _ in xs_lbl],
        "calibration": calibration,
        "y_labels_agree": bool(labels_ok),
    }


def parse_probbars(path: Path) -> dict:
    """IRI figure 3 bars: {season: {la_nina, neutral, el_nino}} in %."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    title = next((c for c in re.findall(r"<!-- (.*?) -->", txt) if "Probabilistic ENSO" in c), None)
    xt, (a, c) = _axes(txt)
    ileg = txt.find('<g id="legend_1">')
    body, leg = txt[:ileg], txt[ileg:]
    colours = {}
    for _, _, b in _blocks(leg, "patch_"):
        m = re.search(r"fill: (#[0-9a-fA-F]{6})", b)
        name = _comment(b)  # the block runs to the next patch and includes the legend text
        if m and name and "Forecast" in name:
            colours[m.group(1).lower()] = (
                "la_nina" if "La Ni" in name else "neutral" if "Neutral" in name else "el_nino"
            )
    xs_lbl = sorted(xt.items(), key=lambda kv: kv[1])
    out: dict[str, dict] = {}
    for _, _, b in _blocks(body, "patch_", indent=3):
        m = re.search(r"fill: (#[0-9a-fA-F]{6})", b)
        p = re.search(r'<path d="([^"]*)"', b)
        if not (m and p) or m.group(1).lower() not in colours:
            continue
        pts = [(float(x), float(y)) for x, y in re.findall(rf"[ML] ({NUM}) ({NUM})", p.group(1))]
        if len(pts) < 4:
            continue
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        xm = (min(xs) + max(xs)) / 2
        lbl = min(xs_lbl, key=lambda kv: abs(kv[1] - xm))[0]
        out.setdefault(lbl, {})[colours[m.group(1).lower()]] = max(ys) - min(ys)  # height in pixels
    # The three bars add up to 100%: normalize by the sum (independent of the y labels, which come
    # out swapped in some old SVGs). The labels are only a cross-check.
    check = []
    for d in out.values():
        s = sum(d.values())
        if np.isfinite(a):
            check.append(abs(abs(a) * s - 100))
        for k in d:
            d[k] = round(100 * d[k] / s, 1) if s else None
    labels_ok = bool(check) and max(check) < 2
    return {"title": title, "prob": out, "colours": colours, "y_labels_agree": labels_ok}


def parse_quicklook(path: Path) -> list[dict]:
    """Probability tables with La Nina / Neutral / El Nino columns, with the heading before them."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    res = []
    for m in re.finditer(r"<table.*?</table>", txt, flags=re.S | re.I):
        t = m.group(0)
        plain = htmlmod.unescape(re.sub(r"<[^>]+>", " ", t))
        if "Neutral" not in plain or "Ni" not in plain:
            continue
        before = htmlmod.unescape(re.sub(r"<[^>]+>", " ", txt[max(0, m.start() - 3000) : m.start()]))
        hs = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", txt[max(0, m.start() - 6000) : m.start()], flags=re.S)
        title = htmlmod.unescape(re.sub(r"<[^>]+>", " ", hs[-1])).strip() if hs else None
        rows = []
        for row in re.findall(r"<tr.*?</tr>", t, flags=re.S | re.I):
            cells = [
                htmlmod.unescape(re.sub(r"<[^>]+>", " ", x)).strip()
                for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S | re.I)
            ]
            if len(cells) >= 4 and re.match(r"^[A-Z]{3}\b", cells[0]):
                try:
                    v = [float(re.sub(r"[^0-9.]", "", x) or "nan") for x in cells[1:4]]
                except ValueError:
                    continue
                rows.append(
                    {"season": cells[0][:3], "label": cells[0], "la_nina": v[0], "neutral": v[1], "el_nino": v[2]}
                )
        pub = re.findall(r"Published:\s*([A-Za-z]+ \d{1,2}, \d{4})", before)
        res.append({"title": title, "published": pub[-1] if pub else None, "rows": rows})
    return res


if __name__ == "__main__":
    import json

    p = Path(sys.argv[1])
    if "figure4" in p.name:
        r = parse_plume(p)
    elif "figure3" in p.name:
        r = parse_probbars(p)
    else:
        r = parse_quicklook(p)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:4000])

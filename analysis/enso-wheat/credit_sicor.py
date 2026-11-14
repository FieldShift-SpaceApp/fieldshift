# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Step 3. Winter-crop operating credit (BCB SICOR, CusteioMunicipioProduto) in the 18 municipalities.

Usage: python -I credit_sicor.py <raw_dir> <results_dir>
Rule: sum by calendar year of issue; real values in BRL of Dec/2025 deflated by the IPCA (BCB SGS
series 433). Nominal value and financed area are reported too, to show which measure gives the
"+2.3% in 2023" figure. Raw OData responses are cached in <raw_dir> (sicor_<product>.json).

Output (results_dir/credit_sicor.json) is a database derived from SICOR, so it stays under the
ODbL like its source (see README).
"""

import json
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import httpx

BASE = "https://olinda.bcb.gov.br/olinda/servico/SICOR/versao/v2/odata/CusteioMunicipioProduto"
IPCA_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"
PRODUCTS = ("TRIGO", "AVEIA", "CEVADA", "CANOLA")  # wheat, oat, barley, canola (SICOR labels)
USER_AGENT = "fieldshift-analysis/1.0"


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def get_json(client, url):
    for t in range(4):
        try:
            r = client.get(url)
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPError, ValueError) as e:
            print(f"attempt {t + 1} failed: {e}", file=sys.stderr)
            time.sleep(4 * (t + 1))
    raise SystemExit(f"giving up on {url}")


def download(client, munis, product, raw: Path):
    """One OData query per municipality; cached in raw_dir with its access time."""
    stamp = raw.with_suffix(".accessed_utc.txt")
    if raw.exists() and stamp.exists():
        return json.loads(raw.read_text(encoding="utf-8")), stamp.read_text(encoding="utf-8")
    rows = []
    for m in munis:
        flt = f"codIbge eq '{m['code']}' and contains(nomeProduto,'{product}')"
        url = f"{BASE}?$filter={quote(flt)}&$top=100000&$format=json"
        v = get_json(client, url)["value"]
        print(f"{product} {m['name']}: {len(v)} rows", file=sys.stderr)
        rows += v
    raw.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    stamp.write_text(now_utc(), encoding="utf-8")
    return rows, stamp.read_text(encoding="utf-8")


def regional_series(rows, idx, base):
    products = sorted({r["nomeProduto"] for r in rows})
    nom, real, area, n = (defaultdict(float) for _ in range(4))
    for r in rows:
        a, mth = int(r["AnoEmissao"]), int(r["MesEmissao"])
        nom[a] += r["VlCusteio"]
        real[a] += r["VlCusteio"] * base / idx[(a, mth)] if (a, mth) in idx else float("nan")
        area[a] += r["AreaCusteio"]
        n[a] += 1
    series = []
    for a in sorted(nom):
        item = {
            "year": a,
            "rows": int(n[a]),
            "nominal_brl": round(nom[a]),
            "real_brl_dec2025": round(real[a]),
            "area_ha": round(area[a]),
        }
        if a - 1 in nom:
            item["change_nominal_pct"] = round(100 * (nom[a] / nom[a - 1] - 1), 1)
            item["change_real_pct"] = round(100 * (real[a] / real[a - 1] - 1), 1)
            item["change_area_pct"] = round(100 * (area[a] / area[a - 1] - 1), 1) if area[a - 1] else None
        series.append(item)
    # January-October cut (the same months every year, because 2026 only runs to October)
    jo_area, jo_real = defaultdict(float), defaultdict(float)
    for r in rows:
        a, mth = int(r["AnoEmissao"]), int(r["MesEmissao"])
        if mth <= 10:
            jo_area[a] += r["AreaCusteio"]
            jo_real[a] += r["VlCusteio"] * base / idx[(a, mth)] if (a, mth) in idx else float("nan")
    jan_oct = []
    for a in sorted(jo_area):
        it = {"year": a, "area_ha": round(jo_area[a]), "real_brl_dec2025": round(jo_real[a])}
        if jo_area.get(a - 1):
            it["change_area_pct"] = round(100 * (jo_area[a] / jo_area[a - 1] - 1), 1)
            it["change_real_pct"] = round(100 * (jo_real[a] / jo_real[a - 1] - 1), 1)
        jan_oct.append(it)
    return {"products_matched": products, "series": series, "jan_oct": jan_oct}


def main() -> None:
    raw_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    munis = json.loads((raw_dir / "municipalities_rs.json").read_text(encoding="utf-8"))
    sources = {}
    with httpx.Client(timeout=180, headers={"User-Agent": USER_AGENT}) as client:
        by_product = {}
        for p in PRODUCTS:
            by_product[p], when = download(client, munis, p, raw_dir / f"sicor_{p.lower()}.json")
            sources[f"sicor_{p.lower()}"] = {
                "url": f"{BASE} (filter codIbge + nomeProduto ~ {p})",
                "accessed_utc": when,
            }
        ipca = get_json(client, IPCA_URL)
        sources["bcb_sgs_433_ipca"] = {"url": IPCA_URL, "accessed_utc": now_utc()}

    # cumulative monthly price index; base Dec/2025
    idx, acc = {}, 1.0
    for p in ipca:
        _, mth, y = p["data"].split("/")
        acc *= 1 + float(p["valor"]) / 100
        idx[(int(y), int(mth))] = acc
    base = idx[(2025, 12)]

    out = {
        "license": "ODbL 1.0 (derived from BCB SICOR, Matriz de Dados do Credito Rural)",
        "sources": sources,
        "municipalities": len(munis),
        "rule": "calendar year of issue; real values in BRL of Dec/2025 (IPCA, SGS 433)",
    }
    keys = {"TRIGO": "wheat", "AVEIA": "oat", "CEVADA": "barley", "CANOLA": "canola"}
    every = []
    for p, rows in by_product.items():
        out[keys[p]] = regional_series(rows, idx, base)
        every += rows
    out["all_winter_crops"] = regional_series(every, idx, base)
    (out_dir / "credit_sicor.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in ("wheat", "oat", "barley", "canola", "all_winter_crops"):
        s = {x["year"]: x for x in out[k]["series"]}
        print(
            k,
            out[k]["products_matched"],
            {
                a: (s[a].get("change_nominal_pct"), s[a].get("change_real_pct"), s[a].get("change_area_pct"))
                for a in (2022, 2023, 2024)
                if a in s
            },
        )
        print(
            "   jan-oct",
            [
                (x["year"], x["area_ha"], x.get("change_area_pct"), x.get("change_real_pct"))
                for x in out[k]["jan_oct"]
                if x["year"] >= 2021
            ],
        )


if __name__ == "__main__":
    main()

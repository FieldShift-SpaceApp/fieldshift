# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Download and aggregate the public sources of the ground-truth test (insured wheat losses x IMERG).

    uv run --with httpx==0.28.1 python -I analysis/ground-truth-proagro/fetch_sources.py <raw_dir> <results_dir>

Sources (all public, no account):
  proagro  BCB Proagro data matrix, "evento" (event) view: municipality x product x event x month of
           issue, already aggregated by the BCB. Kept: wheat (TRIGO) in the 18 Planalto Medio
           municipalities, plus Rio Grande do Sul totals by year x event (context). Names of financial
           institutions are never written.
  coords   IBGE localities API (codes matched by name) and IBGE meshes v3 metadata (centroid, area).
  imerg    NASA POWER Daily API, IMERG_PRECTOT (UTC days), one point per municipality centroid,
           1998-2025. Per municipality and year: Sep-Nov total and days >= 50 mm.

Raw files stay in <raw_dir> (never committed). Small aggregated CSVs and sources.json go to <results_dir>.
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx

RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
CLIENT = httpx.Client(headers={"User-Agent": "fieldshift-analysis/1.0"}, timeout=900, follow_redirects=True)
SOURCES: dict = {}

# The 18 municipalities of analysis/enso-wheat (IBGE codes are looked up by name, never typed by hand)
NAMES = [
    "Cruz Alta", "Ijuí", "Passo Fundo", "Santo Ângelo", "Carazinho", "Panambi", "Tupanciretã",
    "Palmeira das Missões", "Santa Bárbara do Sul", "Júlio de Castilhos", "Ibirubá", "Não-Me-Toque",
    "Condor", "Ajuricaba", "Boa Vista do Cadeado", "Fortaleza dos Valos", "Pejuçara", "Saldanha Marinho",
]  # fmt: skip


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def num(v: str) -> float:
    v = (v or "").strip()
    if v in ("", "-", "..", "..."):
        return 0.0
    try:
        return float(v.replace(".", "").replace(",", ".")) if "," in v else float(v)
    except ValueError:
        return 0.0


def write_csv(name: str, rows: list[dict]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def municipalities() -> dict[str, str]:
    """IBGE code -> name, from the IBGE localities API."""
    p = RAW / "ibge_municipalities_rs.json"
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios"
    if not p.exists():
        r = CLIENT.get(url)
        r.raise_for_status()
        p.write_bytes(r.content)
    code = {m["nome"]: str(m["id"]) for m in json.loads(p.read_text(encoding="utf-8"))}
    missing = [n for n in NAMES if n not in code]
    if missing:
        raise SystemExit(f"municipalities without an IBGE code: {missing}")
    SOURCES.setdefault("ibge_localities", {"url": url, "accessed_utc": now()})
    return {code[n]: n for n in NAMES}


# --- proagro ----------------------------------------------------------------------------------------
BCB = "https://www.bcb.gov.br"
LIST = (
    BCB + "/api/servico/sitebcb/Documentos/byListGuid?tronco=estabilidadefinanceira"
    "&guidLista=a2f0bc74-02f2-4914-938a-81bef9580ee0&ordem=Title%20desc&pasta=%2Fevento"
)
ENROL = ["ADESAO_AREA_AMPARADA_HA", "ADESAO_QTDE_CONTRATOS", "ADESAO_VL_AMPARADO"]
CLAIM = [
    "COP_COMUNICACAO_AREA_HA", "COP_COMUNICACAO_QTDE", "COP_COMUNICACAO_VALOR",
    "COP_DEFERIDA_AREA_HA", "COP_DEFERIDA_QTDE", "COP_DEFERIDA_VALOR_DEFERIDO",
    "COP_ANALISE_AREA_HA", "COP_ANALISE_QTDE",
]  # fmt: skip


def download(url: str, dest: Path) -> None:
    """Stream to the raw folder with retries (large files, unstable network)."""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(4):
        try:
            with CLIENT.stream("GET", url, timeout=httpx.Timeout(60, read=120)) as resp:
                resp.raise_for_status()
                with part.open("wb") as fh:
                    for chunk in resp.iter_bytes(1 << 20):
                        fh.write(chunk)
            part.replace(dest)
            return
        except httpx.HTTPError as exc:
            print("download: retry", attempt + 1, repr(exc), flush=True)
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"download failed: {url}")


def proagro() -> None:
    muns = municipalities()
    lst_p = RAW / "proagro" / "list_evento.json"
    lst_p.parent.mkdir(exist_ok=True)
    r = CLIENT.get(LIST)
    r.raise_for_status()
    lst_p.write_bytes(r.content)
    lst = json.loads(lst_p.read_text(encoding="utf-8"))["conteudo"]
    enrol = defaultdict(lambda: defaultdict(float))  # (mun, year) -> enrolment (all rows)
    ev = defaultdict(lambda: defaultdict(float))  # (mun, year, event) -> claims
    rs_enrol = defaultdict(lambda: defaultdict(float))  # year -> enrolment, RS
    rs_ev = defaultdict(lambda: defaultdict(float))  # (year, event) -> claims, RS
    months = Counter()  # month of issue, wheat RS (contracts)
    files = {}
    for item in sorted(lst, key=lambda x: x["Nome"]):
        dest = RAW / "proagro" / item["Nome"]
        download(BCB + item["Url"], dest)
        files[item["Nome"]] = item["DataPublicacao"]
        with gzip.open(dest, "rt", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f, delimiter=";"):
                if row["PRODUTO"] != "TRIGO" or not row["COD_MUNICIPIO_IBGE"].startswith("43"):
                    continue
                year, month = row["ANO_MES_EMISSAO"][:4], row["ANO_MES_EMISSAO"][5:7]
                months[month] += num(row["ADESAO_QTDE_CONTRATOS"])
                for c in ENROL:
                    rs_enrol[year][c] += num(row[c])
                with_claim = row["SINISTRO"] == "COM SINISTRO"
                e = row["EVENTO"] or "(no event)"
                if with_claim:
                    for c in CLAIM:
                        rs_ev[(year, e)][c] += num(row[c])
                m = row["COD_MUNICIPIO_IBGE"].split(",")[0]
                if m not in muns:
                    continue
                for c in ENROL:
                    enrol[(m, year)][c] += num(row[c])
                if with_claim:
                    for c in CLAIM:
                        ev[(m, year, e)][c] += num(row[c])
        print("proagro", item["Nome"], flush=True)
    write_csv("proagro_wheat_enrolment_by_municipality.csv", [
        {"ibge_code": m, "municipality": muns[m], "issue_year": y, **{c.lower(): round(v[c], 2) for c in ENROL}}
        for (m, y), v in sorted(enrol.items())
    ])  # fmt: skip
    write_csv("proagro_wheat_claims_by_municipality_event.csv", [
        {"ibge_code": m, "municipality": muns[m], "issue_year": y, "event": e,
         **{c.lower(): round(v[c], 2) for c in CLAIM}}
        for (m, y, e), v in sorted(ev.items())
    ])  # fmt: skip
    write_csv(
        "proagro_wheat_rs_enrolment.csv",
        [{"issue_year": y, **{c.lower(): round(v[c], 2) for c in ENROL}} for y, v in sorted(rs_enrol.items())],
    )
    write_csv(
        "proagro_wheat_rs_claims_by_event.csv",
        [
            {"issue_year": y, "event": e, **{c.lower(): round(v[c], 2) for c in CLAIM}}
            for (y, e), v in sorted(rs_ev.items())
        ],
    )
    write_csv(
        "proagro_wheat_rs_issue_month.csv", [{"issue_month": k, "contracts": int(v)} for k, v in sorted(months.items())]
    )
    SOURCES["proagro"] = {
        "page": BCB + "/estabilidadefinanceira/proagro",
        "list_api": LIST,
        "view": "evento (event)",
        "files_published_at": files,
        "accessed_utc": now(),
    }


# --- coords -----------------------------------------------------------------------------------------
def coords() -> None:
    rows = []
    for m, name in municipalities().items():
        url = f"https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{m}/metadados"
        r = CLIENT.get(url)
        r.raise_for_status()
        meta = r.json()[0]
        c = meta["centroide"]
        rows.append({"ibge_code": m, "municipality": name, "lat": c["latitude"], "lon": c["longitude"],
                     "area_km2": meta["area"]["dimensao"]})  # fmt: skip
    write_csv("municipalities.csv", rows)
    SOURCES["ibge_mesh_metadata"] = {
        "url": "https://servicodados.ibge.gov.br/api/v3/malhas/municipios/<code>/metadados",
        "field": "centroide",
        "accessed_utc": now(),
    }


# --- imerg ------------------------------------------------------------------------------------------
POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
START, END = date(1998, 1, 1), date(2025, 12, 31)
HEAVY_MM = 50.0


def imerg() -> None:
    with (OUT / "municipalities.csv").open(encoding="utf-8") as f:
        muns = list(csv.DictReader(f))
    rows, urls, versions = [], {}, set()
    for m in muns:
        params = {
            "parameters": "IMERG_PRECTOT", "community": "AG",
            "longitude": f"{float(m['lon']):.4f}", "latitude": f"{float(m['lat']):.4f}",
            "start": START.strftime("%Y%m%d"), "end": END.strftime("%Y%m%d"),
            "format": "JSON", "time-standard": "UTC",
        }  # fmt: skip
        dest = RAW / "power-imerg" / f"{m['ibge_code']}.json"
        dest.parent.mkdir(exist_ok=True)
        if not dest.exists():
            for attempt in range(4):
                r = CLIENT.get(POWER, params=params)
                if r.status_code == 200:
                    dest.write_bytes(r.content)
                    break
                time.sleep(10 * (attempt + 1))
            else:
                raise RuntimeError(f"POWER {m['municipality']}: HTTP {r.status_code}")
        urls[m["ibge_code"]] = str(httpx.URL(POWER, params=params))
        d = json.loads(dest.read_text(encoding="utf-8"))
        versions.add(str(d.get("header", {}).get("api", {}).get("version", "")))
        fill = float(d.get("header", {}).get("fill_value", -999.0))
        daily = {
            datetime.strptime(k, "%Y%m%d").date(): (None if v is None or v == fill else float(v))
            for k, v in d["properties"]["parameter"]["IMERG_PRECTOT"].items()
        }
        for y in range(START.year, END.year + 1):
            days, dd = [], date(y, 9, 1)
            while dd <= date(y, 11, 30):
                days.append(daily.get(dd))
                dd += timedelta(days=1)
            if any(v is None for v in days):
                continue  # a year enters only with a complete Sep-Nov window
            rows.append({"ibge_code": m["ibge_code"], "municipality": m["municipality"], "year": y,
                         "son_total_mm": round(sum(days), 1),
                         "son_days_ge_50mm": sum(1 for v in days if v >= HEAVY_MM)})  # fmt: skip
        print("imerg", m["municipality"], flush=True)
    write_csv("imerg_son_by_municipality.csv", rows)
    SOURCES["imerg"] = {
        "api": POWER,
        "api_version": sorted(versions),
        "parameter": "IMERG_PRECTOT (UTC days; fill value = missing)",
        "doi": "10.5067/GPM/IMERG/3B-HH/07",
        "urls": urls,
        "rule": "Sep 1 - Nov 30; total and days >= 50 mm; a year only with a complete window",
        "accessed_utc": now(),
    }


if __name__ == "__main__":
    steps = sys.argv[3].split(",") if len(sys.argv) > 3 else ["proagro", "coords", "imerg"]
    path = OUT / "sources.json"
    for s in steps:
        globals()[s]()
        cur = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        cur.update(SOURCES)
        path.write_text(json.dumps(cur, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

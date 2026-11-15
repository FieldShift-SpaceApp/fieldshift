# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Scale of the problem: download the public sources again and check the numbers quoted on the submission page.

    uv run --with httpx==0.28.1 python -I analysis/scale/scale.py [--raw DIR]

Sources (all public, no account):
  IBGE PAM, SIDRA table 1612   wheat planted/harvested area and production, Brazil and Rio Grande do Sul
  IBGE Agricultural Census 2017, SIDRA table 6957   farms (establishments) that produced wheat
  BCB Proagro data matrix, "regiao" view, contracts issued in 2023   approved wheat claims, Rio Grande do Sul
  FAOSTAT Production_Crops_Livestock (bulk, normalized)   wheat harvested area by country, 2024

Each check compares the value recomputed from the source with the number as written in
docs/submission/page-draft.md (fields 2 and 5), at the precision the page uses. Exit code 1 if any check fails.
Raw downloads go to --raw (default ~/.cache/fieldshift/scale; never committed). Results: analysis/scale/results/.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import platform
import sys
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
CLIENT = httpx.Client(headers={"User-Agent": "fieldshift-analysis/1.0"}, timeout=900, follow_redirects=True)
SOURCES: dict = {}

PAM_URL = "https://apisidra.ibge.gov.br/values/t/1612/n1/all/n3/43/v/109,216,214/p/2014-2025/c81/2716"
CENSUS_URL = (
    "https://apisidra.ibge.gov.br/values/t/6957/n1/all/n2/4/n3/43/v/10084/p/2017"
    "/c829/46302/c226/113869,4896,4901,111673,4862/c218/46502/c12517/113601"
)
BCB = "https://www.bcb.gov.br"
PROAGRO_LIST = (
    BCB + "/api/servico/sitebcb/Documentos/byListGuid?tronco=estabilidadefinanceira"
    "&guidLista=a2f0bc74-02f2-4914-938a-81bef9580ee0&ordem=Title%20desc&pasta=%2Fregiao"
)
PROAGRO_FILE = "MATRIZ_PROAGRO_REGIAO_2023.gz"
FAO_URL = "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
FAO_AREAS = ("Argentina", "Uruguay", "Australia", "Brazil", "World")


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def get_json(url: str):
    r = CLIENT.get(url)
    r.raise_for_status()
    return r.json()


def num(v: str) -> float:
    v = (v or "").strip()
    if v in ("", "-", "..", "..."):
        return 0.0
    return float(v.replace(".", "").replace(",", ".")) if "," in v else float(v)


def write_csv(name: str, rows: list[dict]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def pam() -> dict:
    """(place code, variable code, year) -> value. Place 1 = Brazil, 43 = Rio Grande do Sul."""
    d = get_json(PAM_URL)
    assert d[0]["D2C"].startswith("Vari") and d[0]["D3C"].startswith("Ano"), "unexpected SIDRA layout"
    rows = [{"place_code": r["D1C"], "place": r["D1N"], "variable_code": r["D2C"], "variable": r["D2N"],
             "year": r["D3C"], "product": r["D4N"], "value": r["V"], "unit": r["MN"]} for r in d[1:]]  # fmt: skip
    write_csv("ibge_pam_1612_wheat.csv", rows)
    SOURCES["ibge_pam_1612"] = {"url": PAM_URL, "accessed_utc": now()}
    return {(r["place_code"], r["variable_code"], int(r["year"])): num(r["value"]) for r in rows}


def census() -> dict:
    """(place code, product label) -> establishments."""
    d = get_json(CENSUS_URL)
    rows = [{"place_code": r["D1C"], "place": r["D1N"], "variable": r["D2N"], "product_code": r["D5C"],
             "product": r["D5N"], "value": r["V"], "unit": r["MN"]} for r in d[1:]]  # fmt: skip
    write_csv("ibge_census2017_6957_establishments.csv", rows)
    SOURCES["ibge_census_6957"] = {"url": CENSUS_URL, "accessed_utc": now()}
    return {(r["place_code"], r["product"]): num(r["value"]) for r in rows}


def proagro(raw: Path) -> dict:
    """Rio Grande do Sul wheat, contracts issued in 2023: enrolment and approved claims."""
    lst = get_json(PROAGRO_LIST)["conteudo"]
    item = next(i for i in lst if i["Nome"] == PROAGRO_FILE)
    dest = raw / ("proagro_" + PROAGRO_FILE)
    if not dest.exists():
        r = CLIENT.get(BCB + item["Url"])
        r.raise_for_status()
        dest.write_bytes(r.content)
    cols = ["ADESAO_AREA_AMPARADA_HA", "ADESAO_QTDE_CONTRATOS", "COP_DEFERIDA_AREA_HA", "COP_DEFERIDA_QTDE",
            "COP_DEFERIDA_VALOR_DEFERIDO"]  # fmt: skip
    agg = defaultdict(lambda: defaultdict(float))
    with gzip.open(dest, "rt", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["PRODUTO"] != "TRIGO" or not row["COD_MUNICIPIO_IBGE"].startswith("43"):
                continue
            for c in cols:
                agg[row["ANO_MES_EMISSAO"][:4]][c] += num(row[c])
    rows = [{"issue_year": y, "uf": "RS", "product": "TRIGO", **{c.lower(): round(v[c], 2) for c in cols}}
            for y, v in sorted(agg.items())]  # fmt: skip
    write_csv("bcb_proagro_wheat_rs_2023_file.csv", rows)
    SOURCES["bcb_proagro"] = {"page": BCB + "/estabilidadefinanceira/proagro", "list_api": PROAGRO_LIST,
                              "view": "regiao", "file": PROAGRO_FILE, "file_published_at": item["DataPublicacao"],
                              "accessed_utc": now()}  # fmt: skip
    return agg["2023"]


def faostat(raw: Path) -> dict:
    """(area, year) -> wheat harvested area (ha)."""
    dest = raw / "faostat_qcl_normalized.zip"
    if not dest.exists():
        with CLIENT.stream("GET", FAO_URL) as resp:
            resp.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in resp.iter_bytes(1 << 20):
                    fh.write(chunk)
    rows = []
    with zipfile.ZipFile(dest) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv") and "All_Data" in n)
        with z.open(name) as fb:
            for r in csv.DictReader(io.TextIOWrapper(fb, encoding="latin-1")):
                if r["Area"] in FAO_AREAS and r["Item"] == "Wheat" and r["Element"] == "Area harvested" \
                        and int(r["Year"]) >= 2020:  # fmt: skip
                    rows.append({"area": r["Area"], "year": r["Year"], "value": r["Value"], "unit": r["Unit"],
                                 "flag": r.get("Flag", "")})  # fmt: skip
    write_csv("faostat_wheat_area_harvested.csv", rows)
    SOURCES["faostat"] = {"url": FAO_URL, "csv": name, "licence": "CC BY 4.0", "accessed_utc": now()}
    return {(r["area"], int(r["year"])): float(r["value"]) for r in rows}


def check(cid: str, claim: str, value: float, shown: float, expected: float, where: str, source: str) -> dict:
    return {
        "id": cid,
        "claim_on_page": claim,
        "where": where,
        "recomputed": round(value, 4),
        "recomputed_at_page_precision": shown,
        "page_value": expected,
        "match": shown == expected,
        "source": source,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path.home() / ".cache" / "fieldshift" / "scale")
    a = ap.parse_args()
    a.raw.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    started = now()

    p = pam()
    c = census()
    pro = proagro(a.raw)
    fao = faostat(a.raw)

    planted, harvested, production = "109", "216", "214"
    rs25, br25 = p[("43", planted, 2025)], p[("1", planted, 2025)]
    rs_farms = c[("43", "Trigo em grão")]
    prod22, prod23 = p[("43", production, 2022)], p[("43", production, 2023)]
    brl23 = round(pro["COP_DEFERIDA_VALOR_DEFERIDO"], 2)
    pct_area23 = 100 * pro["COP_DEFERIDA_AREA_HA"] / pro["ADESAO_AREA_AMPARADA_HA"]
    three = sum(fao[(k, 2024)] for k in ("Argentina", "Uruguay", "Australia"))
    world = fao[("World", 2024)]
    with_br = 100 * (three + fao[("Brazil", 2024)]) / world
    rs_harv24 = p[("43", harvested, 2024)]
    with_rs = 100 * (three + rs_harv24) / world  # mixes PAM (RS) and FAOSTAT (others): reported, not adopted

    f2, f5 = "page-draft.md field 2", "page-draft.md field 5"
    checks = [
        check("rs_wheat_planted_2025_mha", "Rio Grande do Sul planted 1.16 million hectares of wheat in 2025",
              rs25, round(rs25 / 1e6, 2), 1.16, f2, "IBGE PAM 1612, variable 109"),
        check("rs_share_brazil_wheat_planted_2025_pct", "46% of Brazil's", 100 * rs25 / br25,
              round(100 * rs25 / br25), 46, f2, "IBGE PAM 1612, variable 109"),
        check("rs_wheat_farms_2017", "on about 20,000 farms (2017 Census of Agriculture)", rs_farms,
              round(rs_farms, -3), 20000, f2, "IBGE Census 2017, SIDRA 6957, variable 10084"),
        check("rs_wheat_production_2022_mt", "the state's wheat output fell from 5.3", prod22,
              round(prod22 / 1e6, 1), 5.3, f2, "IBGE PAM 1612, variable 214"),
        check("rs_wheat_production_2023_mt", "to 2.6 million tonnes", prod23, round(prod23 / 1e6, 1), 2.6, f2,
              "IBGE PAM 1612, variable 214"),
        check("rs_wheat_production_2022_mt_2dp", "5.30 Mt (team brief)", prod22, round(prod22 / 1e6, 2), 5.30,
              "team brief", "IBGE PAM 1612, variable 214"),
        check("rs_wheat_production_2023_mt_2dp", "2.59 Mt (team brief)", prod23, round(prod23 / 1e6, 2), 2.59,
              "team brief", "IBGE PAM 1612, variable 214"),
        check("proagro_rs_wheat_2023_approved_bn_brl", "Proagro, approved R$ 2.07 billion in wheat claims", brl23,
              round(brl23 / 1e9, 2), 2.07, f2, "BCB Proagro data matrix, regiao view, 2023 file"),
        check("world_wheat_area_share_ar_uy_au_br_2024_pct", "about 10% of the world's wheat area (AR+UY+AU+BR)",
              with_br, round(with_br), 10, f5, "FAOSTAT QCL 2024, area harvested"),
    ]  # fmt: skip
    context = {
        "rs_wheat_planted_2025_ha": rs25,
        "brazil_wheat_planted_2025_ha": br25,
        "rs_wheat_production_change_2022_2023_pct": round(100 * (prod23 / prod22 - 1), 1),
        "proagro_rs_wheat_2023_insured_ha": round(pro["ADESAO_AREA_AMPARADA_HA"], 2),
        "proagro_rs_wheat_2023_approved_area_ha": round(pro["COP_DEFERIDA_AREA_HA"], 2),
        "proagro_rs_wheat_2023_approved_pct_of_insured_area": round(pct_area23, 1),
        "faostat_2024_ar_uy_au_ha": three,
        "faostat_2024_world_ha": world,
        "world_share_ar_uy_au_2024_pct": round(100 * three / world, 1),
        "world_share_ar_uy_au_br_2024_pct": round(with_br, 1),
        "world_share_ar_uy_au_plus_rs_2024_pct_mixed_sources": round(with_rs, 1),
        "rs_wheat_harvested_2024_ha_pam": rs_harv24,
    }
    out = {"checks": checks, "all_match": all(x["match"] for x in checks), "context": context}
    (OUT / "scale.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (OUT / "sources.json").write_text(json.dumps(SOURCES, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    info = {"started_utc": started, "finished_utc": now(),
            "versions": {"python": platform.python_version(), "httpx": httpx.__version__}}  # fmt: skip
    (OUT / "run_info.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    for x in checks:
        print(("OK  " if x["match"] else "FAIL"), x["id"], x["recomputed_at_page_precision"], "page:", x["page_value"])
    print(json.dumps(context, indent=1))
    sys.exit(0 if out["all_match"] else 1)


if __name__ == "__main__":
    main()

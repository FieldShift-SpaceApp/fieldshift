# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Step 1. Download the primary sources: IBGE localities, IBGE SIDRA table 1612, NOAA CPC ONI,
and the Atlas Digital de Desastres consolidated CSV.

Usage: python -I fetch_sources.py <raw_dir>
Writes into <raw_dir> (outside git): municipalities_rs.json, sidra_1612_v112.json, oni.ascii.txt,
atlas.csv and access_log_fetch.json (URL and access time of every download).
"""

import json
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import httpx

# The 18 municipalities of the Planalto Medio (Rio Grande do Sul) used by the team since the
# Cruz Alta analysis. Names are matched against the IBGE localities API; no code is typed by hand.
TARGET = [
    "Cruz Alta", "Ijuí", "Passo Fundo", "Santo Ângelo", "Carazinho", "Panambi",
    "Tupanciretã", "Palmeira das Missões", "Santa Bárbara do Sul", "Júlio de Castilhos",
    "Ibirubá", "Não-Me-Toque", "Condor", "Ajuricaba", "Boa Vista do Cadeado",
    "Fortaleza dos Valos", "Pejuçara", "Saldanha Marinho",
]  # fmt: skip

LOCALITIES_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios"
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
# Atlas Digital de Desastres no Brasil (MIDR/SEDEC), consolidated CSV v1.1 of 2026-08-06, ~86 MB.
ATLAS_URL = "https://atlasdigital.mdr.gov.br/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv"
USER_AGENT = "fieldshift-analysis/1.0"


def normalize(s: str) -> str:
    # compare names without accents, hyphens or case
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().replace("-", " ").strip()


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def get(client: httpx.Client, url: str) -> httpx.Response:
    for attempt in range(4):
        try:
            r = client.get(url)
            r.raise_for_status()
            return r
        except httpx.HTTPError as e:
            print(f"attempt {attempt + 1} failed for {url}: {e}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"giving up on {url}")


def download_to_file(client: httpx.Client, url: str, dest: Path) -> None:
    """Stream a large file to disk (the Atlas CSV)."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(4):
        try:
            with client.stream("GET", url) as r:
                r.raise_for_status()
                with tmp.open("wb") as fh:
                    for chunk in r.iter_bytes(1 << 20):
                        fh.write(chunk)
            tmp.replace(dest)
            return
        except httpx.HTTPError as e:
            print(f"attempt {attempt + 1} failed for {url}: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise SystemExit(f"giving up on {url}")


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    log = {}
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=300, headers=headers, follow_redirects=True) as client:
        r = get(client, LOCALITIES_URL)
        log["ibge_localities"] = {"url": LOCALITIES_URL, "accessed_utc": now_utc()}
        by_name = {normalize(m["nome"]): m for m in r.json()}
        selected = []
        for name in TARGET:
            m = by_name.get(normalize(name))
            if m is None:
                raise SystemExit(f"municipality not found in the localities API: {name}")
            selected.append({"name": m["nome"], "code": m["id"]})
        path = out / "municipalities_rs.json"
        path.write_text(json.dumps(selected, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(selected)} municipalities matched")

        codes = ",".join(str(m["code"]) for m in selected)
        # v112 = average yield (kg/ha); c81 2713 = soybean, 2716 = wheat; all years
        sidra_url = f"https://apisidra.ibge.gov.br/values/t/1612/n6/{codes}/v/112/p/all/c81/2713,2716/f/a"
        r = get(client, sidra_url)
        (out / "sidra_1612_v112.json").write_text(r.text, encoding="utf-8")
        log["ibge_sidra_1612"] = {"url": sidra_url, "accessed_utc": now_utc()}
        print(f"SIDRA: {len(r.json()) - 1} rows")

        r = get(client, ONI_URL)
        (out / "oni.ascii.txt").write_text(r.text, encoding="utf-8")
        log["noaa_cpc_oni"] = {"url": ONI_URL, "accessed_utc": now_utc()}
        print(f"ONI: {len(r.text.splitlines())} lines")

        # The Atlas file is a fixed release (v1.1 of 2026-08-06): download it once and keep the
        # access time of that download next to it.
        atlas = out / "atlas.csv"
        stamp = out / "atlas.accessed_utc.txt"
        if not (atlas.exists() and stamp.exists()):
            download_to_file(client, ATLAS_URL, atlas)
            stamp.write_text(now_utc(), encoding="utf-8")
        else:
            print("Atlas CSV already in the raw folder; not downloaded again")
        log["atlas_digital_desastres"] = {"url": ATLAS_URL, "accessed_utc": stamp.read_text(encoding="utf-8")}
        print(f"Atlas: {atlas.stat().st_size / 1e6:.1f} MB")

    (out / "access_log_fetch.json").write_text(json.dumps(log, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

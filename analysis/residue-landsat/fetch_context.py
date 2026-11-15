# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Independent check and rain gap: IBGE Censo Agropecuario no-till area for Cruz Alta (2006, 2017), IBGE PAM
summer-crop planted area (same years), and NASA POWER daily rain after the committed cache ends.

    python -I fetch_context.py <raw_dir>

Raw responses go to <raw_dir>/context/ with their URL and access time (never committed).
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx

SIDRA = "https://servicodados.ibge.gov.br/api/v3/agregados"
MUN = "4306106"  # Cruz Alta (RS)
# path + query exactly as sent; SIDRA separators are literal | and [ ]
REQUESTS = {
    # Censo Agropecuario 2006, table 849: establishments and area with no-till on straw ("plantio direto na palha")
    "census_2006_849": f"{SIDRA}/849/periodos/2006/variaveis/2016|2018?localidades=N6[{MUN}]|N3[43]"
    "&classificacao=218[0]|220[0]",
    # Censo Agropecuario 2017, table 6855: establishments by soil preparation system and no-till area
    "census_2017_6855": f"{SIDRA}/6855/periodos/2017/variaveis/9562|9563|9564|9565|2016|2018"
    f"?localidades=N6[{MUN}]|N3[43]&classificacao=829[46302]|12564[41145]|12771[45951]|218[46502]",
    # PAM table 1612, planted area (ha): soybean 2713, maize 2711
    "pam_1612_area": f"{SIDRA}/1612/periodos/2006|2017/variaveis/109?localidades=N6[{MUN}]&classificacao=81[2713,2711]",
}
POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_CACHE_END = date(2026, 10, 31)  # data/cache/power/cruz-alta/daily_19810101_20261031.json


def get(c: httpx.Client, url: str, params: dict | None = None) -> tuple[dict | list, str, str]:
    r = c.get(url, params=params)
    r.raise_for_status()
    return r.json(), str(r.url), datetime.now(UTC).isoformat(timespec="seconds")


def main(raw: Path) -> None:
    out = raw / "context"
    out.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120, headers={"User-Agent": "fieldshift-analysis"}) as c:
        for name, url in REQUESTS.items():
            body, final_url, at = get(c, url)
            (out / f"{name}.json").write_text(
                json.dumps({"url": final_url, "accessed_utc": at, "body": body}, ensure_ascii=False), encoding="utf-8"
            )
            print(name, "ok", flush=True)
        end = date.today() - timedelta(days=1)
        start = POWER_CACHE_END + timedelta(days=1)
        params = {
            "parameters": "PRECTOTCORR",
            "community": "AG",
            "longitude": -53.563,
            "latitude": -28.703,
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "format": "JSON",
        }
        body, final_url, at = get(c, POWER, params)
        (out / "power_prectotcorr_tail.json").write_text(
            json.dumps({"url": final_url, "accessed_utc": at, "body": body}), encoding="utf-8"
        )
        print("power tail ok", start, end, flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))

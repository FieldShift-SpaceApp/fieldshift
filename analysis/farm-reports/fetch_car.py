# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Download the rural-property outlines (CAR, "Área do Imóvel") of one municipality from SICAR's public WFS.

    python -I fetch_car.py [--ibge 4306106] [--raw DIR]

Source: Serviço Florestal Brasileiro (SFB), SICAR GeoServer, layer sicar:sicar_imoveis_<uf>, filtered by
cod_municipio_ibge. The layer has no owner name, CPF or CNPJ; it carries the property code, status, creation
date, declared area, analysis condition, state, municipality, fiscal modules, property type and the outline.

Kept (raw folder only, never committed): outline, property code, declared area (ha), fiscal modules, property
type and status. Dropped at download: creation date and the analysis-condition text. Cancelled records
(status CA) are dropped later, in grids.py. Outputs never carry the CAR code: farms get a sequential number.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_IBGE, raw_dir, write_json  # noqa: E402

WFS = "https://geoserver.car.gov.br/geoserver/sicar/wfs"
UF_BY_PREFIX = {"43": "rs", "42": "sc", "41": "pr", "50": "ms", "51": "mt", "52": "go", "35": "sp", "31": "mg"}
KEEP = ("cod_imovel", "area", "m_fiscal", "tipo_imovel", "status_imovel")


def url_for(ibge: str) -> str:
    uf = UF_BY_PREFIX.get(ibge[:2])
    if uf is None:
        raise SystemExit(f"add the state of IBGE prefix {ibge[:2]} to UF_BY_PREFIX")
    q = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": f"sicar:sicar_imoveis_{uf}",
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "CQL_FILTER": f"cod_municipio_ibge={int(ibge)}",
    }
    return WFS + "?" + urllib.parse.urlencode(q)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ibge", default=DEFAULT_IBGE)
    ap.add_argument("--raw", default=None)
    a = ap.parse_args()
    raw = raw_dir(a.ibge, a.raw)
    url = url_for(a.ibge)
    t0 = datetime.now(UTC)
    req = urllib.request.Request(url, headers={"User-Agent": "fieldshift-analysis/1.0"})
    # The SICAR server only negotiates TLS ciphers that OpenSSL's default security level 2 rejects; level 1 still
    # verifies the certificate and host name.
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
    with urllib.request.urlopen(req, timeout=600, context=ctx) as r:  # noqa: S310 - fixed https URL
        data = json.loads(r.read().decode("utf-8"))
    feats = []
    for f in data["features"]:
        p = f["properties"]
        if int(p["cod_municipio_ibge"]) != int(a.ibge) or f.get("geometry") is None:
            continue
        feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {k: p.get(k) for k in KEEP}})
    out = {"type": "FeatureCollection", "features": feats}
    (raw / "car.geojson").write_text(json.dumps(out), encoding="utf-8")
    write_json(
        raw / "car_access.json",
        {
            "source": "SFB / SICAR public GeoServer (WFS), layer sicar:sicar_imoveis_<uf>",
            "url": url,
            "accessed_utc": t0.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "features_returned": len(data["features"]),
            "features_kept": len(feats),
            "fields_kept": list(KEEP),
            "fields_dropped": "dat_criacao, condicao, uf, municipio, cod_municipio_ibge (no personal fields exist)",
        },
    )
    print(f"CAR {a.ibge}: {len(feats)} outlines -> {raw / 'car.geojson'}")


if __name__ == "__main__":
    main()

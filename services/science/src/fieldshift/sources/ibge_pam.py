# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""IBGE PAM (Produção Agrícola Municipal), SIDRA table 1612, through the IBGE aggregates API v3.

One municipality, one temporary crop (default: soybean, category 2713 of classification 81),
every year the table has: planted area, harvested area, production and average yield. No
credentials. The raw response is kept wrapped with the request URL and the access time (BRT),
like the NASA POWER cache, and the CI only reads recorded responses.

Official statistics have no data type or units in the contracts v1.0.0 (FR9/ADR-7), so this
module writes a plain CSV and a plain provenance JSON, not contract files.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from fieldshift.errors import LayerError, PipelineError
from fieldshift.sources.power import local_now

log = logging.getLogger(__name__)

API_URL = "https://servicodados.ibge.gov.br/api/v3/agregados"
TABLE = "1612"
CLASSIFICATION = "81"  # Produto das lavouras temporárias
SOYBEAN = "2713"  # Soja (em grão)
TABLE_URL = f"https://sidra.ibge.gov.br/tabela/{TABLE}"
METADATA_URL = f"{API_URL}/{TABLE}/metadados"
TIMEOUT_S = 60.0


@dataclass(frozen=True)
class PamVariable:
    code: str
    column: str
    name_pt: str  # as in the table metadata
    unit_pt: str  # as in the table metadata


# Codes, names and units confirmed on METADATA_URL on 2026-11-14.
VARIABLES: tuple[PamVariable, ...] = (
    PamVariable("109", "area_planted_ha", "Área plantada", "Hectares"),
    PamVariable("216", "area_harvested_ha", "Área colhida", "Hectares"),
    PamVariable("214", "production_t", "Quantidade produzida", "Toneladas"),
    PamVariable("112", "yield_kg_ha", "Rendimento médio da produção", "Quilogramas por Hectare"),
)
COLUMNS = ("year", *(v.column for v in VARIABLES))

# SIDRA special values. "-" is a true zero; the others mean no number.
ZERO_SYMBOL = "-"
NO_VALUE_SYMBOLS = frozenset({"..", "...", "X"})


@dataclass(frozen=True)
class PamYear:
    year: int
    area_planted_ha: int | None
    area_harvested_ha: int | None
    production_t: int | None
    yield_kg_ha: int | None


@dataclass(frozen=True)
class PamSeries:
    municipality_id: str
    municipality_name: str
    product_id: str
    product_name: str
    url: str
    accessed_at: str
    years: tuple[PamYear, ...]

    def by_year(self) -> dict[int, PamYear]:
        return {y.year: y for y in self.years}


def build_url(municipality: str, product: str = SOYBEAN) -> str:
    """All periods (`-100` = the last 100 periods) of the four variables for one municipality."""
    if not (municipality.isdigit() and len(municipality) == 7):
        raise PipelineError(f"IBGE municipality code has 7 digits, got {municipality!r}")
    if not product.isdigit():
        raise PipelineError(f"product category must be numeric, got {product!r}")
    codes = "|".join(v.code for v in VARIABLES)
    return (
        f"{API_URL}/{TABLE}/periodos/-100/variaveis/{codes}"
        f"?localidades=N6[{municipality}]&classificacao={CLASSIFICATION}[{product}]"
    )


def cache_name(municipality: str, product: str) -> str:
    return f"pam_{TABLE}_{municipality}_{product}"


def download(url: str, *, client: httpx.Client | None = None) -> list[dict[str, Any]]:
    own = client is None
    client = client or httpx.Client(timeout=TIMEOUT_S)
    try:
        try:
            response = client.get(url)
        except httpx.TransportError as exc:
            raise LayerError("SOURCE_TIMEOUT", f"IBGE API did not respond: {exc}") from exc
    finally:
        if own:
            client.close()
    if response.status_code != 200:
        raise PipelineError(f"IBGE API returned {response.status_code}: {response.text[:300]}")
    return response.json()


def fetch(
    municipality: str,
    product: str,
    *,
    cache_dir: Path,
    offline: bool = False,
    refresh: bool = False,
    client: httpx.Client | None = None,
    now: Callable[[], datetime] = local_now,
) -> PamSeries:
    """Return the PAM series. Idempotent: an existing raw file wins unless `refresh`."""
    url = build_url(municipality, product)
    path = cache_dir / f"{cache_name(municipality, product)}.raw.json"
    if path.exists() and not refresh:
        log.info("IBGE PAM: using %s", path)
        return parse(json.loads(path.read_text(encoding="utf-8")), municipality, product)
    if offline:
        raise LayerError("NOT_EXTRACTED_YET", f"no IBGE PAM file at {path}")
    wrapped = {
        "fieldshift_request": {"url": url, "accessed_at": now().isoformat(timespec="seconds")},
        "response": download(url, client=client),
    }
    series = parse(wrapped, municipality, product)  # validate before writing
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(wrapped, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                    newline="\n")  # fmt: skip
    return series


def _number(text: str) -> int | None:
    if text == ZERO_SYMBOL:
        return 0
    if text in NO_VALUE_SYMBOLS:
        return None
    try:
        return int(text)
    except ValueError as exc:
        raise PipelineError(f"unexpected SIDRA value {text!r}") from exc


def parse(wrapped: dict[str, Any], municipality: str, product: str) -> PamSeries:
    """Check the response (variables, municipality, product) and build one row per year."""
    meta = wrapped["fieldshift_request"]
    by_code = {str(v["id"]): v for v in wrapped["response"]}
    missing = [v.code for v in VARIABLES if v.code not in by_code]
    if missing:
        raise PipelineError(f"IBGE PAM response lacks variables {missing}")

    columns: dict[str, dict[str, str]] = {}
    name = product_name = ""
    for v in VARIABLES:
        result = by_code[v.code]["resultados"]
        if len(result) != 1 or len(result[0]["series"]) != 1:
            raise PipelineError(f"variable {v.code}: expected one result and one series")
        category = result[0]["classificacoes"][0]["categoria"]
        if list(category) != [product]:
            raise PipelineError(f"variable {v.code}: product {list(category)} != {product}")
        series = result[0]["series"][0]
        if series["localidade"]["id"] != municipality:
            raise PipelineError(f"variable {v.code}: municipality {series['localidade']['id']}")
        name, product_name = series["localidade"]["nome"], category[product]
        columns[v.column] = series["serie"]

    years = sorted({int(y) for col in columns.values() for y in col})
    rows = tuple(
        PamYear(year=y, **{c: _number(columns[c].get(str(y), "...")) for c in columns})
        for y in years
    )
    return PamSeries(
        municipality_id=municipality,
        municipality_name=name,
        product_id=product,
        product_name=product_name,
        url=meta["url"],
        accessed_at=meta["accessed_at"],
        years=rows,
    )


def to_csv(series: PamSeries) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(COLUMNS)
    for y in series.years:
        writer.writerow(["" if getattr(y, c) is None else getattr(y, c) for c in COLUMNS])
    return buf.getvalue()


def provenance(series: PamSeries) -> dict[str, Any]:
    """Plain FR19-style record (no contract covers official statistics yet)."""
    first, last = series.years[0].year, series.years[-1].year
    empty = {c: [y.year for y in series.years if getattr(y, c) is None] for c in COLUMNS[1:]}
    empty_note = "; ".join(f"{c}: {years}" for c, years in empty.items() if years) or "none"
    return {
        "dataset": "IBGE Produção Agrícola Municipal (PAM)",
        "provider": "Instituto Brasileiro de Geografia e Estatística (IBGE)",
        "table": f"SIDRA {TABLE}",
        "table_url": TABLE_URL,
        "metadata_url": METADATA_URL,
        "municipality": {"id": series.municipality_id, "name": series.municipality_name},
        "product": {
            "classification": CLASSIFICATION,
            "id": series.product_id,
            "name": series.product_name,
        },  # fmt: skip
        "variables": [
            {"code": v.code, "column": v.column, "name_pt": v.name_pt, "unit_pt": v.unit_pt}
            for v in VARIABLES
        ],
        "temporal": {"resolution": "annual", "period": f"{first}/{last}"},
        "spatial": {"support": "municipality"},
        "access": {
            "url": series.url,
            "accessed_at": series.accessed_at,
            "terms": "IBGE public data; cite IBGE as the source",
        },  # fmt: skip
        "data_type_note": "official statistics (survey), not satellite_observed/modeled",
        "limitations": [
            "PAM year = harvest year: for soybean in RS, year Y is the 1-season harvest "
            "planted in late Y-1 (safra Y-1/Y).",
            "Municipal totals reported by IBGE; not field measurements.",
            "SIDRA symbols: '-' is zero; '..', '...' and 'X' have no value (empty in the CSV).",
            f"Years without a value in this series: {empty_note}.",
        ],
        "si_assisted": "file written by code generated with Claude Code (Anthropic); the "
        "numbers come from the IBGE response, not from the AI",
    }

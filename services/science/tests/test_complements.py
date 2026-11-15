# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Complements (v1.2.0): committed outputs regenerate offline, and the rules behind each number."""

import json
import shutil
from datetime import date

import pytest

from fieldshift.cli import main
from fieldshift.complements import oni as oni_mod
from fieldshift.complements.baresoil import build_bare_soil
from fieldshift.complements.oni import OniFile, load_oni, operational_phases, threshold_phase
from fieldshift.complements.rain_signal import build_rain_signal, season_years, window_days
from fieldshift.complements.replay import build_replay, trend_ratio
from fieldshift.complements.scorecard import _predicted, build_scorecard, load_forecasts
from fieldshift.complements.stage import FILES, oni_period, run_complements
from fieldshift.config import data_dir
from fieldshift.errors import PipelineError
from fieldshift.sources.power_imerg import ImergRaw

SITE = "cruz-alta"
OUT = data_dir() / "sites" / SITE / "output"
INP = data_dir() / "sites" / SITE / "input"


def committed(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


# --- committed outputs -----------------------------------------------------------------------


def test_committed_outputs_regenerate_offline(tmp_path):
    root = tmp_path / "data"
    shutil.copytree(data_dir() / "cache", root / "cache")
    shutil.copytree(data_dir() / "sites" / SITE, root / "sites" / SITE)
    out = run_complements(SITE, data_dir=root, offline=True)
    for key, name in FILES.items():
        assert json.loads(out.paths[key].read_text(encoding="utf-8")) == committed(name), name
    merged = json.loads(out.provenance_path.read_text(encoding="utf-8"))
    assert merged == committed("provenance.json")


def test_scorecard_reproduces_the_research_numbers():
    scores = {s["source_id"]: s for s in committed("forecast-scorecard.json")["scores"]}
    geos = scores["nmme-nasa-geos"]
    assert (geos["n"], geos["el_nino_hits"], geos["el_nino_observed"]) == (41, 4, 7)
    assert (geos["el_nino_forecasts"], geos["false_alarm_ratio"]) == (10, 0.6)
    assert list(scores)[0] == "nmme-nasa-geos"  # NASA GMAO first
    assert {s["issue_month"] for s in scores.values()} == {2}
    assert scores["cpc-iri-official"]["n"] == 12


def test_rain_signal_reproduces_the_research_numbers():
    power = committed("enso-rain-signal.json")["sources"][0]
    by = {p["phase"]: p for p in power["by_phase"]}
    assert power["id"] == "nasa-power"
    assert (by["el_nino"]["n_years"], by["el_nino"]["mean_heavy_days"]) == (15, 1.93)
    assert (by["neutral"]["n_years"], by["neutral"]["mean_heavy_days"]) == (16, 1.12)
    assert (by["la_nina"]["n_years"], by["la_nina"]["mean_heavy_days"]) == (13, 0.92)


def test_replay_counts_wheat_failures_and_keeps_fallow_without_value():
    events = {e["id"]: e for e in committed("replay.json")["events"]}
    vals = {v["id"]: v["value"] for v in events["wheat-failures"]["values"]}
    assert (vals["municipalities_below_75pct"], vals["municipalities"]) == (14, 18)
    assert (vals["municipalities_below_70pct"], vals["municipalities_below_80pct"]) == (11, 16)
    assert (vals["cruz_alta_yield"], vals["cruz_alta_trend"]) == (1500, 2736)
    money = {v["id"] for v in events["winter-paths-2023"]["values"]}
    assert money == {"wheat_margin_operating_cost", "wheat_margin_variable_cost", "cover_crop_cost"}
    assert list(events)[:1] == ["el-nino-watch"]


def test_bare_soil_keeps_the_straw_caveat_and_partner_attribution():
    cal = committed("bare-soil-calendar.json")
    assert "does not separate straw from bare soil" in cal["caveats"][0]["en"]
    assert cal["fortnights"][21]["s2_median_pct"] == 75.6
    records = committed("provenance.json")["records"]
    assert [a["group"] for a in records[cal["s2_provenance_id"]]["attribution"]] == ["partner"]
    assert [a["group"] for a in records[cal["modis_provenance_id"]]["attribution"]] == ["nasa"]


def test_every_complement_record_declares_its_attribution():
    records = committed("provenance.json")["records"]
    ids = {i for name in FILES.values() for _, i in _refs(committed(name))}
    assert len(ids) > 10
    for rid in ids:
        assert records[rid]["attribution"], rid
        for upstream in records[rid]["inputs"]:
            if not upstream.startswith("prov:power:"):  # POWER records predate v1.2.0
                assert records[upstream]["attribution"], upstream


def _refs(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k.endswith("provenance_id") and isinstance(v, str):
                yield path, v
            else:
                yield from _refs(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _refs(v, f"{path}[{i}]")


# --- rules -----------------------------------------------------------------------------------


def _oni(values: dict) -> OniFile:
    return OniFile(values=values, url="https://x", accessed_at="2026-11-14T00:00:00-03:00",
                   sha256="0")  # fmt: skip


def test_operational_phase_needs_five_consecutive_seasons():
    seasons = oni_mod.SEASONS
    four = {(s, 2000): (0.6 if i < 4 else 0.0) for i, s in enumerate(seasons)}
    five = {(s, 2001): (0.6 if i < 5 else -0.6 if i >= 7 else 0.0) for i, s in enumerate(seasons)}
    phases = operational_phases(_oni({**four, **five}))
    assert phases[("DJF", 2000)] == "neutral"
    assert phases[("DJF", 2001)] == phases[("AMJ", 2001)] == "el_nino"
    assert phases[("JAS", 2001)] == "la_nina"  # JAS..NDJ 2001 = 5 seasons <= -0.5
    assert threshold_phase(0.5) == "el_nino" and threshold_phase(-0.49) == "neutral"


def test_oni_file_is_checked_against_its_sha(tmp_path):
    shutil.copytree(data_dir() / "cache" / "noaa", tmp_path / "noaa")
    assert load_oni(tmp_path / "noaa").values[("JJA", 2023)] == 1.0
    (tmp_path / "noaa" / "oni.ascii.txt").write_text("changed", encoding="ascii")
    with pytest.raises(PipelineError, match="sha256"):
        load_oni(tmp_path / "noaa")


def test_oni_period_spans_december_before_the_first_djf():
    period = oni_period(_oni({("DJF", 1950): 0.0, ("NDJ", 1951): 0.0}))
    assert (period.start, period.end) == ("1949-12-01", "1952-01-31")


def test_probability_tie_goes_to_neutral():
    assert _predicted((0.1, 0.45, 0.45)) == "neutral"
    assert _predicted((0.04, 0.47, 0.49)) == "el_nino"


def test_scorecard_rejects_other_issue_months():
    rows = load_forecasts(INP / "enso-forecasts.csv")
    oni = load_oni(data_dir() / "cache" / "noaa")
    bad = [{**rows[0], "issue_month": "3"}]
    with pytest.raises(PipelineError, match="only February"):
        build_scorecard(SITE, bad, oni, "2026-11-14T19:46:32-03:00")


def test_incomplete_window_is_skipped():
    days = {d: 10.0 for d in window_days(2020)}
    days[date(2020, 10, 3)] = None
    days |= {d: (60.0 if d.day == 1 else 0.0) for d in window_days(2021)}
    out = season_years(days, range(2020, 2022))
    assert out[2020] is None
    assert out[2021] == (180.0, 3)


def test_imerg_with_only_fill_values_is_declared(tmp_path):
    oni = load_oni(data_dir() / "cache" / "noaa")
    days = {d: 1.0 for y in range(1982, 2026) for d in window_days(y)}
    empty = ImergRaw(lat=0, lon=0, url="https://x", accessed_at="2026-11-14T00:00:00-03:00",
                     api_version="v2", native_unit="mm/day",
                     daily={date(2000, 1, 1): None})  # fmt: skip
    doc, _ = build_rain_signal(SITE, days, empty, days, oni)
    assert [s.id for s in doc.sources] == ["nasa-power", "ana-2853015"]
    assert "-999" in doc.notes[0].en


def test_trend_ratio_needs_ten_years():
    series = {y: 1000.0 + 10 * (y - 1981) for y in range(1981, 1990)}
    assert trend_ratio(series, 1985) is None
    series[1990] = 1090.0
    trend, ratio = trend_ratio(series, 1985)
    assert trend == pytest.approx(1040.0) and ratio == pytest.approx(1.0)


def test_missing_inputs_fail_clearly(tmp_path):
    with pytest.raises(PipelineError, match="replay input missing"):
        build_replay(SITE, tmp_path)
    with pytest.raises(PipelineError, match="bare-soil input missing"):
        build_bare_soil(SITE, tmp_path)


def test_cli_complements_offline(tmp_path, capsys):
    root = tmp_path / "data"
    shutil.copytree(data_dir() / "cache", root / "cache")
    shutil.copytree(data_dir() / "sites" / SITE, root / "sites" / SITE)
    assert main(["complements", "--site", SITE, "--offline", "--data-dir", str(root)]) == 0
    assert "provenance records" in capsys.readouterr().out
    shutil.rmtree(root / "cache" / "power-imerg")
    assert main(["complements", "--site", SITE, "--offline", "--data-dir", str(root)]) == 1
    assert "no IMERG cache" in capsys.readouterr().err


# --- now-2026 (v1.3.0) -----------------------------------------------------------------------


def test_now_2026_numbers_and_cutoffs():
    doc = committed("now-2026.json")
    power, imerg = doc["sources"]
    assert (power["id"], imerg["id"]) == ("nasa-power", "gpm-imerg")
    assert power["window"] == {"start": "2026-09-01", "end": "2026-11-11"}
    assert (power["total_mm"], power["heavy_days"], power["wettest_day"]) == (
        935.3,
        5,
        "2026-11-04",
    )
    assert [m["total_mm"] for m in power["months"]] == [246.3, 381.1, 307.9]
    assert imerg["window"] == {"start": "2026-09-01", "end": "2026-09-14"}  # POWER lag at access
    assert (imerg["total_mm"], imerg["heavy_days"]) == (54.0, 1)
    assert power["same_days"][0]["year"] == 2023
    by = {p["phase"]: p for p in power["by_phase"]}
    assert {p: by[p]["n_years"] for p in by} == {"el_nino": 9, "neutral": 10, "la_nina": 9}
    assert doc["current"] == {
        "season": "ASO", "year": 2026, "oni": 2.46, "phase": "el_nino",
        "provenance_id": "prov:noaa:cruz-alta:oni",
    }  # fmt: skip


def test_now_2026_keeps_reports_apart_with_url_and_attribution():
    doc = committed("now-2026.json")
    records = committed("provenance.json")["records"]
    assert [r["published"] for r in doc["reported"]] == ["2026-10-22", "2026-11-12"]
    for r in doc["reported"]:
        assert r["url"].startswith("https://www.emater.tche.br/")
        rec = records[r["provenance_id"]]
        assert rec["data_type"] == "user_provided" and rec["refs"][0]["url"] == r["url"]
        assert "IBGE PAM" in rec["limitations"][0]["en"]
    for s in doc["sources"]:
        rec = records[s["provenance_id"]]
        assert [a["group"] for a in rec["attribution"]] == ["nasa", "other_public"]
        assert all(i in records for i in rec["inputs"])


def test_now_window_uses_the_same_calendar_days_and_stops_at_a_gap():
    from fieldshift.complements.now import last_valid_day, same_days, window_values

    daily = {date(2026, 9, d): 1.0 for d in range(1, 11)}
    daily[date(2026, 9, 5)] = None
    assert last_valid_day(daily, date(2026, 9, 1), date(2026, 11, 13)) == date(2026, 9, 4)
    with pytest.raises(PipelineError):
        last_valid_day({}, date(2026, 9, 1), date(2026, 11, 13))
    days = same_days(2023, date(2026, 9, 1), date(2026, 9, 3))
    assert days == [date(2023, 9, 1), date(2023, 9, 2), date(2023, 9, 3)]
    assert window_values({d: 2.0 for d in days[:2]}, days) is None

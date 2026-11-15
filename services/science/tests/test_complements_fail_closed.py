# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Complements fail closed: an incomplete re-run stops with PipelineError (and the path) instead
of writing a different number. Regression tests for the Codex review of 3774ab4 (PR #42)."""

import csv
import importlib.util
import json
import shutil
from datetime import date
from pathlib import Path

import httpx
import pytest

from fieldshift.complements import now as now_mod
from fieldshift.complements.oni import load_oni, operational_phases
from fieldshift.complements.rain_signal import build_rain_signal, window_days
from fieldshift.complements.replay import MUNICIPALITIES, TARGET_YEAR, build_replay, load_yields
from fieldshift.complements.stage import power_rain
from fieldshift.config import data_dir
from fieldshift.errors import PipelineError
from fieldshift.sites import resolve_site
from fieldshift.sources.power_imerg import ImergRaw

SITE = "cruz-alta"
INP = data_dir() / "sites" / SITE / "input"
POWER_CACHE = data_dir() / "cache" / "power" / SITE / "daily_19810101_20261031.json"


# --- 1. POWER history: chosen by coverage, not by file name ----------------------------------


def _power_cache(folder: Path, name: str, keep=lambda d: True, change=None) -> Path:
    wrapped = json.loads(POWER_CACHE.read_text(encoding="utf-8"))
    for code, series in wrapped["response"]["properties"]["parameter"].items():
        kept = {k: v for k, v in series.items() if keep(date(int(k[:4]), int(k[4:6]), int(k[6:])))}
        if change and code == "PRECTOTCORR":
            kept[change] = kept[change] + 1.0
        wrapped["response"]["properties"]["parameter"][code] = kept
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(json.dumps(wrapped), encoding="utf-8")
    return path


def test_power_rain_picks_the_complete_cache_whatever_its_name(tmp_path):
    site = resolve_site(SITE, data_dir())
    folder = tmp_path / "cache" / "power" / SITE
    _power_cache(folder, "daily_19810101_20261031.json")
    # sorts last and its name claims more, but it stops in 1999
    _power_cache(folder, "daily_19810101_20991231.json", keep=lambda d: d.year < 2000)
    rain = power_rain(tmp_path, SITE, site.lat, site.lon)
    assert rain[date(2025, 11, 30)] is not None


def test_power_rain_fails_when_no_cache_covers_the_window(tmp_path):
    site = resolve_site(SITE, data_dir())
    folder = tmp_path / "cache" / "power" / SITE
    _power_cache(folder, "daily_19810101_20261031.json", keep=lambda d: d.year < 2000)
    with pytest.raises(PipelineError, match="no NASA POWER cache covers") as err:
        power_rain(tmp_path, SITE, site.lat, site.lon)
    assert "daily_19810101_20261031.json" in str(err.value)
    with pytest.raises(PipelineError, match="no NASA POWER cache in"):
        power_rain(tmp_path, "other-site", site.lat, site.lon)


def test_power_rain_refuses_two_equal_caches_that_disagree(tmp_path):
    site = resolve_site(SITE, data_dir())
    folder = tmp_path / "cache" / "power" / SITE
    _power_cache(folder, "daily_a.json")
    _power_cache(folder, "daily_b.json", change="20101015")
    with pytest.raises(PipelineError, match="different PRECTOTCORR values"):
        power_rain(tmp_path, SITE, site.lat, site.lon)
    _power_cache(folder, "daily_b.json")  # same values: no ambiguity
    assert power_rain(tmp_path, SITE, site.lat, site.lon)[date(2010, 10, 15)] is not None


# --- 2. forecast archive script: retries, manifest, atomic publish ---------------------------


def _script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "enso_forecast_inputs.py"
    spec = importlib.util.spec_from_file_location("enso_forecast_inputs", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeClient:
    """Answers from a list of outcomes per call: an int status, bytes (200) or an exception."""

    def __init__(self, outcomes, default=404):
        self.outcomes, self.default, self.calls = list(outcomes), default, []

    def get(self, url):
        self.calls.append(url)
        out = self.outcomes.pop(0) if self.outcomes else self.default
        if isinstance(out, Exception):
            raise out
        if isinstance(out, bytes):
            return httpx.Response(200, content=out)
        return httpx.Response(out, content=b"")


def test_fetch_retries_timeouts_and_server_errors_then_writes(tmp_path):
    mod, waits = _script(), []
    client = FakeClient([httpx.ReadTimeout("slow"), 503, b"payload"])
    dest = tmp_path / "raw" / "f.svg"
    assert mod.fetch(client, "https://x/f", dest, sleep=waits.append) == dest
    assert dest.read_bytes() == b"payload" and len(client.calls) == 3
    assert waits[:2] == [mod.BACKOFF_S, mod.BACKOFF_S * 2]  # exponential backoff
    assert not list(dest.parent.glob("*.tmp"))


def test_fetch_gives_up_without_leaving_a_file(tmp_path):
    mod = _script()
    dest = tmp_path / "f.svg"
    always = FakeClient([], default=httpx.ConnectTimeout("down"))
    assert mod.fetch(always, "https://x/f", dest, sleep=lambda s: None) is None
    assert len(always.calls) == mod.RETRIES and not dest.exists()
    gone = FakeClient([404, b"never asked"])
    assert mod.fetch(gone, "https://x/f", dest, sleep=lambda s: None) is None
    assert len(gone.calls) == 1  # a definitive status is not retried


def _committed_rows(mod) -> list[list]:
    with (INP / "enso-forecasts.csv").open(encoding="utf-8", newline="") as fh:
        return [list(r) for r in list(csv.reader(fh))[1:]]


def test_manifest_matches_the_committed_csv_byte_for_byte():
    mod = _script()
    rows = _committed_rows(mod)
    assert mod.missing_coverage(rows) == []
    assert mod.csv_bytes(rows) == (INP / "enso-forecasts.csv").read_bytes()
    assert sum(len(y) for y in mod.EXPECTED.values()) == len(rows) == 121


def test_incomplete_archive_leaves_the_canonical_files_untouched(tmp_path):
    mod = _script()
    out, oni_out = tmp_path / "input", tmp_path / "noaa"
    out.mkdir()
    shutil.copy(INP / "enso-forecasts.csv", out / "enso-forecasts.csv")
    oni_out.mkdir()
    (oni_out / "oni.ascii.txt").write_bytes(b"old oni")
    before = (out / "enso-forecasts.csv").read_bytes()
    rows = [r for r in _committed_rows(mod) if not (r[0] == "iri-objective" and r[2] == "2010")]
    with pytest.raises(mod.CoverageError, match="iri-objective 2010"):
        mod.publish(rows, b"new oni", "2026-11-14T00:00:00-03:00", out, oni_out)
    assert (out / "enso-forecasts.csv").read_bytes() == before
    assert (oni_out / "oni.ascii.txt").read_bytes() == b"old oni"
    mod.publish(_committed_rows(mod), b"new oni", "2026-11-14T00:00:00-03:00", out, oni_out)
    assert (out / "enso-forecasts.csv").read_bytes() == before
    assert (oni_out / "oni.ascii.txt").read_bytes() == b"new oni"
    assert not list(out.glob("*.tmp")) and not list(oni_out.glob("*.tmp"))


def test_failing_network_aborts_the_run_without_publishing(tmp_path, capsys):
    mod = _script()
    out, oni_out = tmp_path / "input", tmp_path / "noaa"
    out.mkdir()
    (out / "enso-forecasts.csv").write_bytes(b"canonical")
    oni_text = (data_dir() / "cache" / "noaa" / "oni.ascii.txt").read_bytes()
    # ONI answers; every archive file then fails: the NMME climatology is missing
    client = FakeClient([oni_text], default=404)
    argv = ["--cache", str(tmp_path / "raw"), "--out", str(out), "--oni-out", str(oni_out)]
    assert mod.main(argv, client=client) == 1
    assert "nothing published" in capsys.readouterr().out
    assert (out / "enso-forecasts.csv").read_bytes() == b"canonical"
    assert not oni_out.exists()


# --- 3. heavy-rain signal: one record per metric, period and n from complete windows ----------


def test_rain_signal_records_per_metric_with_their_own_period_and_sample():
    oni = load_oni(data_dir() / "cache" / "noaa")
    power = {d: 1.0 for y in range(1982, 2026) for d in window_days(y)}
    gauge = dict(power)
    for y in (1990, 2025):
        gauge[date(y, 10, 1)] = None  # gaps: those windows are not complete
    imerg = ImergRaw(lat=0, lon=0, url="https://x", accessed_at="2026-11-14T00:00:00-03:00",
                     api_version="v2", native_unit="mm/day",
                     daily={d: 2.0 for y in range(2001, 2026) for d in window_days(y)})  # fmt: skip
    doc, recs = build_rain_signal(SITE, power, imerg, gauge, oni)
    by_id = {r.id: r for r in recs}
    for src, (start, end, n, gaps) in {
        "nasa-power": ("1982-09-01", "2025-11-30", 44, "none"),
        "gpm-imerg": ("2001-09-01", "2025-11-30", 25, "none"),
        "ana-2853015": ("1982-09-01", "2024-11-30", 42, "1990,2025"),
    }.items():
        head = by_id[f"prov:computed:{SITE}:enso-heavy-rain:{src}"]
        assert head.variable.unit == "1"
        assert head.inputs == [f"{head.id}:{k}" for k in ("heavy-days", "total", "n-years")]
        units = {
            k: by_id[f"{head.id}:{k}"].variable.unit for k in ("heavy-days", "total", "n-years")
        }
        assert units == {"heavy-days": "days", "total": "mm", "n-years": "count"}
        for rid in [head.id, *head.inputs]:
            rec = by_id[rid]
            assert (rec.temporal.period.start, rec.temporal.period.end) == (start, end), rid
            assert rec.method.parameters["complete_years"] == n, rid
            assert rec.method.parameters["incomplete_years"] == gaps, rid
        assert by_id[head.inputs[0]].inputs == by_id[head.inputs[1]].inputs  # upstream + ONI
    signal = {s.id: s for s in doc.sources}
    assert sum(p.n_years for p in signal["ana-2853015"].by_phase) == 42


# --- 4. replay: exactly the 18 municipalities, target year and history for each --------------


def _replay_input(tmp_path) -> Path:
    shutil.copy(INP / "replay-2023.yaml", tmp_path / "replay-2023.yaml")
    shutil.copytree(INP / "ibge-wheat", tmp_path / "ibge-wheat")
    return tmp_path / "ibge-wheat"


def _rewrite(path: Path, edit) -> None:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    fields = list(rows[0])
    rows = [r for r in (edit(r) for r in rows) if r is not None]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def test_replay_input_is_the_declared_18_municipalities(tmp_path):
    folder = _replay_input(tmp_path)
    assert len(MUNICIPALITIES) == 18 and set(load_yields(folder)) == MUNICIPALITIES
    timeline, _ = build_replay(SITE, tmp_path)
    assert "14 of 18" in next(e for e in timeline.events if e.id == "wheat-failures").title.en
    (folder / "pam_1612_4316709_2716.csv").unlink()
    with pytest.raises(PipelineError, match=r"missing \['4316709'\]") as err:
        build_replay(SITE, tmp_path)
    assert str(folder) in str(err.value)
    shutil.copy(INP / "ibge-wheat" / "pam_1612_4316709_2716.csv", folder)
    shutil.copy(folder / "pam_1612_4316709_2716.csv", folder / "pam_1612_4399999_2716.csv")
    with pytest.raises(PipelineError, match=r"unexpected \['4399999'\]"):
        build_replay(SITE, tmp_path)


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda r: None if r["year"] == str(TARGET_YEAR) else r, "no 2023 wheat yield"),
        (lambda r: {**r, "yield_kg_ha": ""} if r["year"] == str(TARGET_YEAR) else r,
         "no 2023 wheat yield"),
        (lambda r: {**r, "yield_kg_ha": "0"} if r["year"] == str(TARGET_YEAR) else r,
         "SIDRA '-' = no harvest"),
        (lambda r: r if int(r["year"]) >= 2017 else {**r, "yield_kg_ha": ""},
         "the trend needs at least 10"),
    ],
    ids=["row-absent", "empty-cell", "zero", "short-history"],
)  # fmt: skip
def test_replay_member_without_target_year_or_history_fails_with_its_path(tmp_path, edit, message):
    folder = _replay_input(tmp_path)
    path = folder / "pam_1612_4310009_2716.csv"
    _rewrite(path, edit)
    with pytest.raises(PipelineError, match=message) as err:
        build_replay(SITE, tmp_path)
    assert str(path) in str(err.value)


def test_replay_history_zero_stays_out_of_the_trend_but_is_not_absent(tmp_path):
    folder = _replay_input(tmp_path)
    path = folder / "pam_1612_4306106_2716.csv"
    base = load_yields(folder)["4306106"]
    _rewrite(path, lambda r: {**r, "yield_kg_ha": "0"} if r["year"] == "1990" else r)
    assert 1990 in base and 1990 not in load_yields(folder)["4306106"]  # zero = no harvest


# --- now-2026: the climatology must be complete ----------------------------------------------


def test_now_climatology_with_a_gap_fails():
    oni = load_oni(data_dir() / "cache" / "noaa")
    phases = operational_phases(oni)
    end = date(2026, 9, 14)
    full = {
        d: 1.0
        for y in range(now_mod.CLIM_FIRST, now_mod.CLIM_LAST + 1)
        for d in now_mod.same_days(y, now_mod.START, end)
    }
    assert len(now_mod.climatology_values("gpm-imerg", full, end, phases)) == 28
    full[date(2005, 9, 3)] = None
    with pytest.raises(PipelineError, match=r"gpm-imerg: .*\[2005\]"):
        now_mod.climatology_values("gpm-imerg", full, end, phases)

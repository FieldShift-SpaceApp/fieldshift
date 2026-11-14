# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""NASA POWER fetcher: parsing, cache, retry/backoff.

No network: a recorded response and httpx.MockTransport.
"""

import copy
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from fieldshift.errors import LayerError, PipelineError
from fieldshift.sources import power

FIXTURE = Path(__file__).parent / "fixtures" / "power" / "dev-floripa_daily_20240101_20240229.json"
LAT, LON = -27.6, -48.5
START, END = date(2024, 1, 1), date(2024, 2, 29)


@pytest.fixture
def wrapped() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def no_network_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected network call: {request.url}")

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parse_recorded_response(wrapped):
    raw = power.parse(wrapped, lat=LAT, lon=LON)
    assert raw.api_version.startswith("v2.")
    assert raw.time_standard == "LST"
    assert raw.first_day == START and raw.last_day == END
    assert set(raw.daily) == {p.code for p in power.PARAMS}
    assert len(raw.daily["T2M"]) == 60
    assert raw.elevation_m == pytest.approx(210.76)
    assert raw.accessed_at.endswith("-03:00")


def test_fill_value_becomes_none_never_a_number(wrapped):
    wrapped["response"]["properties"]["parameter"]["PRECTOTCORR"]["20240110"] = -999.0
    raw = power.parse(wrapped, lat=LAT, lon=LON)
    assert raw.daily["PRECTOTCORR"][date(2024, 1, 10)] is None


def test_unit_drift_is_rejected(wrapped):
    wrapped["response"]["parameters"]["ALLSKY_SFC_SW_DWN"]["units"] = "kW-hr/m^2/day"
    with pytest.raises(PipelineError, match="native unit"):
        power.parse(wrapped, lat=LAT, lon=LON)


def test_cache_for_another_point_is_rejected(wrapped):
    with pytest.raises(PipelineError, match="requested"):
        power.parse(wrapped, lat=-23.5, lon=LON)


def test_api_error_payload_is_reported(wrapped):
    bad = {"fieldshift_request": wrapped["fieldshift_request"],
           "response": {"messages": ["Please remove the duplicates"]}}  # fmt: skip
    with pytest.raises(PipelineError, match="no data"):
        power.parse(bad, lat=LAT, lon=LON)


def test_existing_cache_wins_and_no_request_is_made(tmp_path, wrapped):
    path = power.cache_path(tmp_path, "dev-floripa", START, END)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(wrapped), encoding="utf-8")
    raw = power.fetch("dev-floripa", LAT, LON, START, END, cache_root=tmp_path,
                      client=no_network_client())  # fmt: skip
    assert (
        raw.daily["T2M"][START] == wrapped["response"]["properties"]["parameter"]["T2M"]["20240101"]
    )


def test_offline_without_cache_fails_with_layer_reason(tmp_path):
    with pytest.raises(LayerError) as exc:
        power.fetch("dev-floripa", LAT, LON, START, END, cache_root=tmp_path, offline=True)
    assert exc.value.code == "NOT_EXTRACTED_YET"


def test_download_retries_5xx_with_backoff_then_caches(tmp_path, wrapped):
    calls: list[httpx.Request] = []
    replies = [
        httpx.Response(503),
        httpx.Response(429),
        httpx.Response(200, json=wrapped["response"]),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return replies[len(calls) - 1]

    sleeps: list[float] = []
    fixed_now = datetime(2026, 11, 14, 14, 0, tzinfo=timezone(timedelta(hours=-3)))
    raw = power.fetch(
        "dev-floripa", LAT, LON, START, END, cache_root=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=sleeps.append, now=lambda: fixed_now,
    )  # fmt: skip
    assert len(calls) == 3 and sleeps == [2.0, 4.0]
    q = calls[0].url.params
    assert q["community"] == "AG" and q["start"] == "20240101" and q["end"] == "20240229"
    assert q["parameters"].split(",") == [p.code for p in power.PARAMS]
    assert "EVPTRNS" not in q["parameters"]
    cached = json.loads(power.cache_path(tmp_path, "dev-floripa", START, END).read_text())
    assert cached["fieldshift_request"]["accessed_at"] == "2026-11-14T14:00:00-03:00"
    assert raw.accessed_at == "2026-11-14T14:00:00-03:00"


def test_client_error_is_not_retried(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(422, json={"messages": ["bad parameter"]})

    with pytest.raises(PipelineError, match="422"):
        power.download({}, client=httpx.Client(transport=httpx.MockTransport(handler)),
                       sleep=lambda s: None)  # fmt: skip
    assert len(calls) == 1


def test_network_down_gives_source_timeout_after_all_attempts():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectError("down", request=request)

    with pytest.raises(LayerError) as exc:
        power.download({}, client=httpx.Client(transport=httpx.MockTransport(handler)),
                       sleep=lambda s: None)  # fmt: skip
    assert exc.value.code == "SOURCE_TIMEOUT"
    assert len(calls) == power.MAX_ATTEMPTS


def test_bad_payload_is_never_cached(tmp_path, wrapped):
    broken = copy.deepcopy(wrapped["response"])
    del broken["properties"]["parameter"]["GWETROOT"]

    def handler(request):
        return httpx.Response(200, json=broken)

    with pytest.raises(PipelineError, match="GWETROOT"):
        power.fetch("dev-floripa", LAT, LON, START, END, cache_root=tmp_path,
                    client=httpx.Client(transport=httpx.MockTransport(handler)))  # fmt: skip
    assert not power.cache_path(tmp_path, "dev-floripa", START, END).exists()


def test_default_end_is_last_day_of_previous_month():
    assert power.default_end(date(2026, 11, 14)) == date(2026, 10, 31)
    assert power.default_end(date(2024, 3, 1)) == date(2024, 2, 29)

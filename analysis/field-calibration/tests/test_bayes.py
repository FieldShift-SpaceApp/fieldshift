# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Checks of the Bayesian ruler: it reproduces the Embrapa fit, and uncertainty only falls with new points."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bayes  # noqa: E402
import calibrate  # noqa: E402


def test_vague_prior_reproduces_the_embrapa_quadratic():
    m, _, _ = bayes.embrapa_posterior()
    x = np.linspace(0.015, 0.10, 12)
    np.testing.assert_allclose(bayes.basis(x) @ m, bayes.embrapa.cover(x), atol=0.05)


def test_no_local_point_means_posterior_equals_prior(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("id,date,method,pct_straw,ndti,ndvi\n", encoding="utf-8")
    assert calibrate.read_measurements(f) == []


def test_public_file_with_coordinates_is_refused(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("id,lat,lon,pct_straw,ndti\nx,-28.6,-53.6,80,0.1\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        calibrate.read_measurements(f)


def test_green_canopy_reading_is_skipped(tmp_path):
    f = tmp_path / "green.csv"
    f.write_text("id,pct_straw,ndti,ndvi\na,80,0.10,0.6\nb,85,0.09,0.2\n", encoding="utf-8")
    assert [r["id"] for r in calibrate.read_measurements(f)] == ["b"]


@pytest.mark.parametrize("x_new", [0.02, 0.06, 0.11, 0.17])
def test_one_more_point_never_increases_uncertainty(x_new):
    _, s0, sigma = bayes.transfer_prior(0.5)
    red = bayes.reduction_pct(s0, x_new, sigma, np.linspace(0, 0.2, 21))
    assert (red >= -1e-9).all()


def test_uncertainty_does_not_depend_on_measured_cover():
    m0, s0, sigma = bayes.transfer_prior(0.5)
    _, s_a = bayes.update(m0, s0, [0.05, 0.09], [10, 20], sigma)
    _, s_b = bayes.update(m0, s0, [0.05, 0.09], [70, 99], sigma)
    np.testing.assert_allclose(s_a, s_b)


def test_power_answer_is_stable():
    p = calibrate.power_analysis()
    assert p["B_does_ndti_respond_85_vs_95"]["fields_per_group_needed"] == 24
    assert p["C_ropes_per_field"]["ropes_needed_tau_0"] == 3
    assert p["A_satellite_one_field"]["best_case_probability_of_right_side"] < 0.75

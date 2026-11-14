import pytest

from fieldshift import __version__
from fieldshift.cli import main


def test_main_without_arguments_returns_zero():
    assert main([]) == 0


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_unknown_flag_fails():
    with pytest.raises(SystemExit) as exc:
        main(["--no-such-flag"])
    assert exc.value.code == 2

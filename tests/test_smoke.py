from typer.testing import CliRunner

from caliper import __version__
from caliper.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_demo_runs_offline() -> None:
    result = runner.invoke(app, ["demo", "--steps", "3"])
    assert result.exit_code == 0
    assert "demo ok" in result.stdout


def test_stub_exit_code() -> None:
    result = runner.invoke(app, ["run", "x"])
    assert result.exit_code == 2

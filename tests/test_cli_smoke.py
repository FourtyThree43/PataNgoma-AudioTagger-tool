from click.testing import CliRunner

from patangoma.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "PataNgoma AudioTagger CLI" in result.output
    assert "show" in result.output
    assert "update" in result.output
    assert "delete" in result.output
    assert "search" in result.output
    assert "scan" in result.output
    assert "plan" in result.output
    assert "apply" in result.output
    assert "rollback" in result.output
    assert "doctor" in result.output

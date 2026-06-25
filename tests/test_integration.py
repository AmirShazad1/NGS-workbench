from click.testing import CliRunner

from pipeline.main import cli


def test_run_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "Run the full NGS pipeline" in result.output


def test_run_requires_config_and_output():
    runner = CliRunner()
    result = runner.invoke(cli, ["run"])
    assert result.exit_code != 0


def test_run_batch_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["run-batch", "--help"])
    assert result.exit_code == 0
    assert "sample sheet" in result.output.lower()


def test_run_with_invalid_config_path_fails():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--config", "does_not_exist.yaml", "--output", "out/"])
    assert result.exit_code != 0

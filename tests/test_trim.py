from unittest.mock import patch

import pytest

from pipeline.stages.trim import trim_paired, trim_single


@patch("pipeline.stages.trim.subprocess.run")
def test_trim_single_builds_expected_command(mock_run, tmp_path):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""

    output_dir = tmp_path / "trimmed"
    result = trim_single("reads.fastq", output_dir, threads=2)

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "fastp"
    assert "-i" in cmd and "reads.fastq" in cmd
    assert result.endswith("trimmed.fastq.gz")


@patch("pipeline.stages.trim.subprocess.run")
def test_trim_paired_builds_expected_command(mock_run, tmp_path):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""

    output_dir = tmp_path / "trimmed"
    r1, r2 = trim_paired("r1.fastq", "r2.fastq", output_dir, threads=4)

    cmd = mock_run.call_args[0][0]
    assert "-I" in cmd and "r2.fastq" in cmd
    assert r1.endswith("trimmed_R1.fastq.gz")
    assert r2.endswith("trimmed_R2.fastq.gz")


@patch("pipeline.stages.trim.subprocess.run")
def test_trim_single_raises_on_failure(mock_run, tmp_path):
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "boom"

    with pytest.raises(RuntimeError, match="fastp error"):
        trim_single("reads.fastq", tmp_path / "trimmed")

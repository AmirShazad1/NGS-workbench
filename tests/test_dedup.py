from unittest.mock import patch

import pytest

from pipeline.stages.dedup import mark_duplicates


@patch("pipeline.stages.dedup.subprocess.run")
def test_mark_duplicates_runs_expected_command_sequence(mock_run, tmp_path):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""

    input_bam = tmp_path / "aligned.bam"
    output_bam = tmp_path / "dedup.bam"
    work_dir = tmp_path / "tmp"

    mark_duplicates(input_bam, output_bam, work_dir)

    commands = [call.args[0][0:2] for call in mock_run.call_args_list]
    assert commands == [
        ["samtools", "sort"],
        ["samtools", "fixmate"],
        ["samtools", "sort"],
        ["samtools", "markdup"],
        ["samtools", "index"],
    ]


@patch("pipeline.stages.dedup.subprocess.run")
def test_mark_duplicates_raises_on_failure(mock_run, tmp_path):
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "boom"

    with pytest.raises(RuntimeError):
        mark_duplicates(tmp_path / "in.bam", tmp_path / "out.bam", tmp_path / "tmp")

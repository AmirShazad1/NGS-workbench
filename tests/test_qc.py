import gzip
from unittest.mock import patch

from pipeline.stages.qc import parse_fastq_basic, run_fastqc

FASTQ_CONTENT = "@read1\nACGTACGTAC\n+\nIIIIIIIIII\n" "@read2\nTTTTGGGGCC\n+\n!!!!!!!!!!\n"


def test_parse_fastq_basic_plain(tmp_path):
    fq = tmp_path / "test.fastq"
    fq.write_text(FASTQ_CONTENT)

    stats = parse_fastq_basic(fq)

    assert stats["reads"] == 2
    assert stats["total_bases"] == 20
    assert stats["avg_quality"] > 0


def test_parse_fastq_basic_gzip(tmp_path):
    fq = tmp_path / "test.fastq.gz"
    with gzip.open(fq, "wt") as f:
        f.write(FASTQ_CONTENT)

    stats = parse_fastq_basic(fq)

    assert stats["reads"] == 2
    assert stats["total_bases"] == 20


def test_parse_fastq_basic_empty_file(tmp_path):
    fq = tmp_path / "empty.fastq"
    fq.write_text("")

    stats = parse_fastq_basic(fq)

    assert stats["reads"] == 0
    assert stats["avg_quality"] == 0
    assert stats["reads_per_mb"] == 0


@patch("pipeline.stages.qc.subprocess.run")
def test_run_fastqc_success(mock_run, tmp_path):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""

    output_dir = tmp_path / "qc"
    result = run_fastqc(["data/test.fastq"], output_dir)

    assert result == output_dir
    args = mock_run.call_args[0][0]
    assert args[0] == "fastqc"
    assert "data/test.fastq" in args


@patch("pipeline.stages.qc.subprocess.run")
def test_run_fastqc_failure_raises(mock_run, tmp_path):
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "boom"

    import pytest

    with pytest.raises(RuntimeError, match="FastQC error"):
        run_fastqc(["data/test.fastq"], tmp_path / "qc")

from unittest.mock import MagicMock, patch

import pytest

from pipeline.stages.align import align_reads, index_reference, reference_is_indexed


def make_index_files(tmp_path, ref_name="reference.fasta"):
    ref = tmp_path / ref_name
    ref.write_text(">chr1\nACGT\n")
    for suffix in (".amb", ".ann", ".bwt", ".pac", ".sa"):
        (tmp_path / f"{ref_name}{suffix}").write_text("")
    return ref


def test_reference_is_indexed_false_when_missing(tmp_path):
    ref = tmp_path / "reference.fasta"
    ref.write_text(">chr1\nACGT\n")
    assert reference_is_indexed(ref) is False


def test_reference_is_indexed_true_when_present(tmp_path):
    ref = make_index_files(tmp_path)
    assert reference_is_indexed(ref) is True


@patch("pipeline.stages.align.subprocess.run")
def test_index_reference_skips_when_already_indexed(mock_run, tmp_path):
    ref = make_index_files(tmp_path)
    index_reference(ref)
    mock_run.assert_not_called()


@patch("pipeline.stages.align.subprocess.run")
def test_index_reference_runs_when_missing(mock_run, tmp_path):
    ref = tmp_path / "reference.fasta"
    ref.write_text(">chr1\nACGT\n")
    mock_run.return_value.returncode = 0
    index_reference(ref)
    mock_run.assert_called_once()
    assert mock_run.call_args[0][0][:2] == ["bwa", "index"]


@patch("pipeline.stages.align.subprocess.run")
@patch("pipeline.stages.align.subprocess.Popen")
def test_align_reads_single_end_builds_correct_command(mock_popen, mock_run, tmp_path):
    bwa_proc = MagicMock()
    bwa_proc.returncode = 0
    bwa_proc.communicate.return_value = (b"", b"")
    sort_proc = MagicMock()
    sort_proc.returncode = 0
    sort_proc.communicate.return_value = (b"", b"")
    mock_popen.side_effect = [bwa_proc, sort_proc]

    output_bam = tmp_path / "aligned.bam"
    align_reads("ref.fasta", output_bam, fastq_file="reads.fastq", threads=2)

    bwa_cmd = mock_popen.call_args_list[0][0][0]
    assert bwa_cmd == ["bwa", "mem", "-t", "2", "ref.fasta", "reads.fastq"]


@patch("pipeline.stages.align.subprocess.run")
@patch("pipeline.stages.align.subprocess.Popen")
def test_align_reads_paired_end_builds_correct_command(mock_popen, mock_run, tmp_path):
    bwa_proc = MagicMock()
    bwa_proc.returncode = 0
    bwa_proc.communicate.return_value = (b"", b"")
    sort_proc = MagicMock()
    sort_proc.returncode = 0
    sort_proc.communicate.return_value = (b"", b"")
    mock_popen.side_effect = [bwa_proc, sort_proc]

    output_bam = tmp_path / "aligned.bam"
    align_reads("ref.fasta", output_bam, fastq_r1="r1.fastq", fastq_r2="r2.fastq", threads=4)

    bwa_cmd = mock_popen.call_args_list[0][0][0]
    assert bwa_cmd == ["bwa", "mem", "-t", "4", "ref.fasta", "r1.fastq", "r2.fastq"]


def test_align_reads_requires_input(tmp_path):
    with pytest.raises(ValueError):
        align_reads("ref.fasta", tmp_path / "out.bam")

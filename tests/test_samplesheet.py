import pytest

from pipeline.utils.samplesheet import load_sample_sheet


def write_csv(path, text):
    path.write_text(text)


def test_load_sample_sheet_single_and_paired(tmp_path):
    sheet = tmp_path / "sheet.csv"
    write_csv(
        sheet,
        (
            "sample_id,fastq_input,fastq_r1,fastq_r2,reference_genome\n"
            "s1,data/s1.fastq,,,\n"
            "s2,,data/s2_R1.fastq,data/s2_R2.fastq,\n"
        ),
    )
    base_config = {"reference_genome": "data/ref.fasta", "threads": 4}
    samples = load_sample_sheet(sheet, base_config, tmp_path / "out")

    assert len(samples) == 2
    assert samples[0]["sample_id"] == "s1"
    assert samples[0]["fastq_input"] == "data/s1.fastq"
    assert samples[0]["reference_genome"] == "data/ref.fasta"
    assert str(samples[0]["output_dir"]).endswith("s1")

    assert samples[1]["sample_id"] == "s2"
    assert samples[1]["fastq_r1"] == "data/s2_R1.fastq"
    assert samples[1]["fastq_r2"] == "data/s2_R2.fastq"


def test_load_sample_sheet_duplicate_id_raises(tmp_path):
    sheet = tmp_path / "sheet.csv"
    write_csv(sheet, ("sample_id,fastq_input\n" "s1,data/a.fastq\n" "s1,data/b.fastq\n"))
    with pytest.raises(ValueError, match="duplicate"):
        load_sample_sheet(sheet, {"reference_genome": "ref.fasta"}, tmp_path / "out")


def test_load_sample_sheet_missing_fastq_raises(tmp_path):
    sheet = tmp_path / "sheet.csv"
    write_csv(sheet, "sample_id,fastq_input\ns1,\n")
    with pytest.raises(ValueError, match="fastq_input"):
        load_sample_sheet(sheet, {"reference_genome": "ref.fasta"}, tmp_path / "out")


def test_load_sample_sheet_missing_reference_raises(tmp_path):
    sheet = tmp_path / "sheet.csv"
    write_csv(sheet, "sample_id,fastq_input\ns1,data/a.fastq\n")
    with pytest.raises(ValueError, match="reference_genome"):
        load_sample_sheet(sheet, {}, tmp_path / "out")


def test_load_sample_sheet_empty_raises(tmp_path):
    sheet = tmp_path / "sheet.csv"
    write_csv(sheet, "sample_id,fastq_input\n")
    with pytest.raises(ValueError, match="no data rows"):
        load_sample_sheet(sheet, {"reference_genome": "ref.fasta"}, tmp_path / "out")

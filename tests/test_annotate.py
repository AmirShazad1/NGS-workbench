import gzip
from unittest.mock import patch

from pipeline.stages.annotate import annotate_variants, parse_annotation

VCF_BODY = (
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    "chr1\t100\t.\tA\tG\t50\tPASS\tDP=20;ANN=G|missense_variant|MODERATE|GENE1\n"
)


def test_parse_annotation_extracts_ann_field(tmp_path):
    vcf = tmp_path / "annotated.vcf.gz"
    with gzip.open(vcf, "wt") as f:
        f.write(VCF_BODY)

    records = parse_annotation(vcf)

    assert len(records) == 1
    assert records[0]["chrom"] == "chr1"
    assert records[0]["pos"] == "100"
    assert "missense_variant" in records[0]["annotation"]


@patch("pipeline.stages.annotate.shutil.which", return_value=None)
def test_annotate_variants_falls_back_when_snpeff_missing(mock_which, tmp_path):
    input_vcf = tmp_path / "variants.vcf.gz"
    with gzip.open(input_vcf, "wt") as f:
        f.write(VCF_BODY)

    output_vcf = tmp_path / "annotated.vcf.gz"
    result = annotate_variants(input_vcf, output_vcf, genome_build="GRCh38")

    assert result == str(output_vcf)
    assert output_vcf.exists()
    with gzip.open(output_vcf, "rt") as f:
        assert f.read() == VCF_BODY


@patch("pipeline.stages.annotate.subprocess.run")
@patch("pipeline.stages.annotate.shutil.which")
def test_annotate_variants_uses_configured_genome_build(mock_which, mock_run, tmp_path):
    mock_which.side_effect = lambda name: "/usr/bin/snpEff" if name == "snpEff" else None

    input_vcf = tmp_path / "variants.vcf.gz"
    with gzip.open(input_vcf, "wt") as f:
        f.write(VCF_BODY)
    output_vcf = tmp_path / "annotated.vcf.gz"

    def fake_run(cmd, stdout=None, stderr=None, text=None, check=None):
        if cmd[0] == "/usr/bin/snpEff":
            if stdout is not None:
                stdout.write(VCF_BODY)
            from unittest.mock import MagicMock

            return MagicMock(returncode=0, stderr="")
        if cmd[0] == "bgzip":
            annotated_plain = output_vcf.parent / "annotated.vcf"
            annotated_plain.rename(output_vcf.parent / "annotated.vcf.gz")
            from unittest.mock import MagicMock

            return MagicMock(returncode=0, stderr="")
        from unittest.mock import MagicMock

        return MagicMock(returncode=0, stderr="")

    mock_run.side_effect = fake_run

    annotate_variants(input_vcf, output_vcf, genome_build="GRCh37")

    snpeff_cmd = [c.args[0] for c in mock_run.call_args_list if c.args[0][0] == "/usr/bin/snpEff"][0]
    assert "GRCh37" in snpeff_cmd

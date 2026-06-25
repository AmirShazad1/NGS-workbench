import gzip
from unittest.mock import MagicMock, patch

from pipeline.stages.variant_call import call_variants, count_variants

VCF_BODY = (
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    "chr1\t100\t.\tA\tG\t50\tPASS\tDP=20\n"
    "chr1\t200\t.\tC\tT\t30\tPASS\tDP=15\n"
)


def test_count_variants_plain(tmp_path):
    vcf = tmp_path / "variants.vcf"
    vcf.write_text(VCF_BODY)
    assert count_variants(vcf) == 2


def test_count_variants_gzip(tmp_path):
    vcf = tmp_path / "variants.vcf.gz"
    with gzip.open(vcf, "wt") as f:
        f.write(VCF_BODY)
    assert count_variants(vcf) == 2


@patch("pipeline.stages.variant_call.subprocess.run")
@patch("pipeline.stages.variant_call.subprocess.Popen")
def test_call_variants_pipes_mpileup_into_call_and_filters_depth(mock_popen, mock_run, tmp_path):
    mpileup_proc = MagicMock()
    mpileup_proc.communicate.return_value = (b"", b"")
    call_proc = MagicMock()
    call_proc.returncode = 0
    call_proc.communicate.return_value = (b"", b"")
    mpileup_proc.returncode = 0
    mock_popen.side_effect = [mpileup_proc, call_proc]
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""

    reference = tmp_path / "ref.fasta"
    reference.write_text(">chr1\nACGT\n")
    (tmp_path / "ref.fasta.fai").write_text("chr1\t4\t6\t4\t5\n")

    output_vcf = tmp_path / "variants.vcf.gz"

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["bcftools", "view"]:
            with gzip.open(output_vcf, "wt") as out:
                out.write(VCF_BODY)
        return MagicMock(returncode=0, stderr="")

    mock_run.side_effect = fake_run

    result = call_variants(tmp_path / "input.bam", reference, output_vcf, min_depth=10)

    mpileup_cmd = mock_popen.call_args_list[0][0][0]
    assert mpileup_cmd[:2] == ["bcftools", "mpileup"]
    call_cmd = mock_popen.call_args_list[1][0][0]
    assert call_cmd[:2] == ["bcftools", "call"]
    assert result == str(output_vcf)
    assert output_vcf.exists()

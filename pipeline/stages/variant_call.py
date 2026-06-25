import gzip
import subprocess
from pathlib import Path

from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)


def call_variants(bam_file, reference_fasta, output_vcf, min_depth=10):
    """Call variants with `bcftools mpileup | bcftools call`, then filter
    on read depth (`min_depth`), which the legacy `samtools mpileup` path
    accepted as a config option but never actually applied.
    """
    output_vcf = Path(output_vcf)
    output_vcf.parent.mkdir(parents=True, exist_ok=True)
    raw_vcf = output_vcf.with_name(output_vcf.name.replace(".vcf.gz", ".raw.vcf.gz"))

    _ensure_fasta_index(reference_fasta)

    logger.info(f"Calling variants from {bam_file} against {reference_fasta}...")

    mpileup_cmd = ["bcftools", "mpileup", "-f", str(reference_fasta), "-q", "20", "-Ou", str(bam_file)]
    call_cmd = ["bcftools", "call", "-mv", "-Oz", "-o", str(raw_vcf)]

    logger.info(f"Running: {' '.join(mpileup_cmd)} | {' '.join(call_cmd)}")

    mpileup_proc = subprocess.Popen(mpileup_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    call_proc = subprocess.Popen(call_cmd, stdin=mpileup_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mpileup_proc.stdout.close()

    _, call_stderr = call_proc.communicate()
    _, mpileup_stderr = mpileup_proc.communicate()

    if mpileup_proc.returncode != 0:
        logger.error(f"bcftools mpileup failed: {mpileup_stderr.decode()}")
        raise RuntimeError(f"bcftools mpileup error: {mpileup_stderr.decode()}")
    if call_proc.returncode != 0:
        logger.error(f"bcftools call failed: {call_stderr.decode()}")
        raise RuntimeError(f"bcftools call error: {call_stderr.decode()}")

    _filter_by_depth(raw_vcf, output_vcf, min_depth)
    raw_vcf.unlink(missing_ok=True)

    subprocess.run(["bcftools", "index", "-t", "-f", str(output_vcf)], check=True)

    logger.info(f"Variant calling complete: {output_vcf}")
    return str(output_vcf)


def _ensure_fasta_index(reference_fasta):
    fai_path = Path(str(reference_fasta) + ".fai")
    if fai_path.exists():
        return
    result = subprocess.run(["samtools", "faidx", str(reference_fasta)], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"samtools faidx failed: {result.stderr}")
        raise RuntimeError(f"samtools faidx error: {result.stderr}")


def _filter_by_depth(raw_vcf, output_vcf, min_depth):
    cmd = ["bcftools", "view", "-i", f"DP>={min_depth}", "-Oz", "-o", str(output_vcf), str(raw_vcf)]
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"bcftools view (depth filter) failed: {result.stderr}")
        raise RuntimeError(f"bcftools view error: {result.stderr}")


def count_variants(vcf_file):
    """Count non-header records in a (gzip or plain) VCF file."""
    opener = gzip.open if str(vcf_file).endswith(".gz") else open
    count = 0
    with opener(vcf_file, "rt") as f:
        for line in f:
            if not line.startswith("#"):
                count += 1
    return count

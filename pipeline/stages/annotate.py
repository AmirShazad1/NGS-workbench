import gzip
import shutil
import subprocess
from pathlib import Path

from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)


def snpeff_available():
    return shutil.which("snpEff") is not None or shutil.which("snpeff") is not None


def annotate_variants(input_vcf, output_vcf, genome_build="hg38"):
    """Annotate variants with SnpEff using the configured `genome_build`
    (previously hardcoded to hg38 regardless of the actual reference used).
    Falls back to copying the VCF unchanged if SnpEff isn't installed.
    """
    output_vcf = Path(output_vcf)
    output_vcf.parent.mkdir(parents=True, exist_ok=True)

    snpeff_bin = shutil.which("snpEff") or shutil.which("snpeff")
    if not snpeff_bin:
        logger.warning("SnpEff not found on PATH - copying VCF unchanged")
        shutil.copy(input_vcf, output_vcf)
        return str(output_vcf)

    logger.info(f"Annotating variants with SnpEff ({genome_build})...")

    input_path = Path(input_vcf)
    decompressed = input_path
    cleanup_decompressed = False
    if input_path.suffix == ".gz":
        decompressed = output_vcf.parent / input_path.name[:-3]
        with gzip.open(input_path, "rt") as src, open(decompressed, "w") as dst:
            dst.write(src.read())
        cleanup_decompressed = True

    annotated_plain = output_vcf.parent / "annotated.vcf"
    cmd = [snpeff_bin, genome_build, str(decompressed)]
    logger.info(f"Running: {' '.join(cmd)}")

    with open(annotated_plain, "w") as out_f:
        result = subprocess.run(cmd, stdout=out_f, stderr=subprocess.PIPE, text=True)

    if cleanup_decompressed:
        decompressed.unlink(missing_ok=True)

    if result.returncode != 0:
        logger.error(f"SnpEff failed: {result.stderr}")
        raise RuntimeError(f"SnpEff error: {result.stderr}")

    subprocess.run(["bgzip", "-f", str(annotated_plain)], check=True)
    bgzipped = annotated_plain.with_suffix(annotated_plain.suffix + ".gz")
    bgzipped.rename(output_vcf)

    logger.info(f"Annotation complete: {output_vcf}")
    return str(output_vcf)


def parse_annotation(vcf_file, limit=None):
    """Extract basic variant + ANN-field data from an annotated VCF."""
    opener = gzip.open if str(vcf_file).endswith(".gz") else open
    records = []
    with opener(vcf_file, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            if limit is not None and len(records) >= limit:
                break
            fields = line.strip().split("\t")
            if len(fields) < 5:
                continue
            chrom, pos, _, ref, alt = fields[0], fields[1], fields[2], fields[3], fields[4]
            qual = fields[5] if len(fields) > 5 else None
            info = fields[7] if len(fields) > 7 else ""

            ann = ""
            for entry in info.split(";"):
                if entry.startswith("ANN="):
                    ann = entry[len("ANN=") :]
                    break

            records.append(
                {
                    "chrom": chrom,
                    "pos": pos,
                    "ref": ref,
                    "alt": alt,
                    "qual": qual,
                    "annotation": ann,
                }
            )

    return records

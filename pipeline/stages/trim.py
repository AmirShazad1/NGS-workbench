import subprocess
from pathlib import Path

from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)


def trim_single(fastq_file, output_dir, threads=4):
    """Adapter/quality-trim a single-end FASTQ file with fastp."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trimmed = output_dir / "trimmed.fastq.gz"
    report_html = output_dir / "fastp.html"
    report_json = output_dir / "fastp.json"

    cmd = [
        "fastp",
        "-i",
        str(fastq_file),
        "-o",
        str(trimmed),
        "-w",
        str(threads),
        "-h",
        str(report_html),
        "-j",
        str(report_json),
    ]
    _run_fastp(cmd)
    logger.info(f"Trimming complete: {trimmed}")
    return str(trimmed)


def trim_paired(fastq_r1, fastq_r2, output_dir, threads=4):
    """Adapter/quality-trim a paired-end FASTQ pair with fastp."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trimmed_r1 = output_dir / "trimmed_R1.fastq.gz"
    trimmed_r2 = output_dir / "trimmed_R2.fastq.gz"
    report_html = output_dir / "fastp.html"
    report_json = output_dir / "fastp.json"

    cmd = [
        "fastp",
        "-i",
        str(fastq_r1),
        "-I",
        str(fastq_r2),
        "-o",
        str(trimmed_r1),
        "-O",
        str(trimmed_r2),
        "-w",
        str(threads),
        "-h",
        str(report_html),
        "-j",
        str(report_json),
    ]
    _run_fastp(cmd)
    logger.info(f"Trimming complete: {trimmed_r1}, {trimmed_r2}")
    return str(trimmed_r1), str(trimmed_r2)


def _run_fastp(cmd):
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"fastp failed: {result.stderr}")
        raise RuntimeError(f"fastp error: {result.stderr}")

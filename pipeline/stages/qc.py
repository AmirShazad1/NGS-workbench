import gzip
import subprocess
from pathlib import Path

from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)


def run_fastqc(fastq_files, output_dir):
    """Run FastQC on one or more input FASTQ file(s). FastQC handles
    gzip-compressed input natively, so no decompression is needed here."""
    if isinstance(fastq_files, (str, Path)):
        fastq_files = [fastq_files]

    logger.info(f"Running FastQC on {', '.join(str(f) for f in fastq_files)}...")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["fastqc", "-o", str(output_dir), "--quiet", *[str(f) for f in fastq_files]]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"FastQC failed: {result.stderr}")
        raise RuntimeError(f"FastQC error: {result.stderr}")

    logger.info(f"FastQC completed. Results in {output_dir}")
    return output_dir


def _open_fastq(fastq_file):
    fastq_file = str(fastq_file)
    if fastq_file.endswith(".gz"):
        return gzip.open(fastq_file, "rt")
    return open(fastq_file, "r")


def parse_fastq_basic(fastq_file):
    """Parse a FASTQ file (plain or gzip-compressed) and return basic stats."""
    read_count = 0
    total_bases = 0
    quality_sum = 0
    quality_count = 0

    with _open_fastq(fastq_file) as f:
        for i, line in enumerate(f):
            position = i % 4
            if position == 1:
                seq = line.strip()
                read_count += 1
                total_bases += len(seq)
            elif position == 3:
                qual = line.strip()
                quality_sum += sum(ord(q) - 33 for q in qual)
                quality_count += len(qual)

    avg_quality = quality_sum / quality_count if quality_count else 0

    return {
        "reads": read_count,
        "total_bases": total_bases,
        "avg_quality": round(avg_quality, 2),
        "reads_per_mb": round(read_count / (total_bases / 1e6), 0) if total_bases > 0 else 0,
    }

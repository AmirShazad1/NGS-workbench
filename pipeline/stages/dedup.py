import subprocess
from pathlib import Path

from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)


def mark_duplicates(input_bam, output_bam, work_dir):
    """Mark duplicate reads following samtools' recommended workflow:
    name-sort -> fixmate -> coordinate-sort -> markdup -> index.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    namesorted_bam = work_dir / "namesorted.bam"
    fixmate_bam = work_dir / "fixmate.bam"
    possorted_bam = work_dir / "possorted.bam"

    logger.info(f"Marking duplicates in {input_bam}...")

    _run(["samtools", "sort", "-n", "-o", str(namesorted_bam), str(input_bam)])
    _run(["samtools", "fixmate", "-m", str(namesorted_bam), str(fixmate_bam)])
    _run(["samtools", "sort", "-o", str(possorted_bam), str(fixmate_bam)])
    _run(["samtools", "markdup", str(possorted_bam), str(output_bam)])
    _run(["samtools", "index", str(output_bam)])

    for intermediate in (namesorted_bam, fixmate_bam, possorted_bam):
        intermediate.unlink(missing_ok=True)

    logger.info(f"Duplicate marking complete: {output_bam}")
    return str(output_bam)


def _run(cmd):
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Command failed ({' '.join(cmd)}): {result.stderr}")
        raise RuntimeError(f"dedup step error: {result.stderr}")

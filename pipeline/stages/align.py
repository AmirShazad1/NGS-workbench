import subprocess
from pathlib import Path

from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)

BWA_INDEX_SUFFIXES = (".amb", ".ann", ".bwt", ".pac", ".sa")


def reference_is_indexed(reference_fasta):
    reference_fasta = Path(reference_fasta)
    return all(Path(str(reference_fasta) + suffix).exists() for suffix in BWA_INDEX_SUFFIXES)


def index_reference(reference_fasta, force=False):
    """Index reference genome with BWA, skipping work if already indexed."""
    if not force and reference_is_indexed(reference_fasta):
        logger.info(f"Reference already indexed, skipping: {reference_fasta}")
        return

    logger.info(f"Indexing reference genome: {reference_fasta}")
    cmd = ["bwa", "index", str(reference_fasta)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"BWA indexing failed: {result.stderr}")
        raise RuntimeError(f"BWA indexing error: {result.stderr}")

    logger.info("Reference indexed")


def align_reads(reference_fasta, output_bam, fastq_file=None, fastq_r1=None, fastq_r2=None, threads=4):
    """Align single-end (`fastq_file`) or paired-end (`fastq_r1`+`fastq_r2`)
    reads to the reference using BWA-MEM, then sort and index the result."""
    if fastq_r1 and fastq_r2:
        reads = [str(fastq_r1), str(fastq_r2)]
        logger.info(f"Aligning paired-end reads {fastq_r1}, {fastq_r2} to {reference_fasta}...")
    elif fastq_file:
        reads = [str(fastq_file)]
        logger.info(f"Aligning single-end reads {fastq_file} to {reference_fasta}...")
    else:
        raise ValueError("align_reads requires either fastq_file or both fastq_r1/fastq_r2")

    cmd = ["bwa", "mem", "-t", str(threads), str(reference_fasta), *reads]
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        bwa_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        sort_cmd = ["samtools", "sort", "-o", str(output_bam), "-"]
        sort_proc = subprocess.Popen(sort_cmd, stdin=bwa_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bwa_proc.stdout.close()

        _, sort_stderr = sort_proc.communicate()
        _, bwa_stderr = bwa_proc.communicate()

        if bwa_proc.returncode != 0:
            logger.error(f"BWA mem failed: {bwa_stderr.decode()}")
            raise RuntimeError(f"BWA mem error: {bwa_stderr.decode()}")

        if sort_proc.returncode != 0:
            logger.error(f"Samtools sort failed: {sort_stderr.decode()}")
            raise RuntimeError(f"Sort error: {sort_stderr.decode()}")

        subprocess.run(["samtools", "index", str(output_bam)], check=True)
        logger.info(f"Alignment complete: {output_bam}")

    except Exception as e:
        logger.error(f"Alignment failed: {str(e)}")
        raise

    return str(output_bam)

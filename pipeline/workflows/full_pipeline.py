from pathlib import Path

from pipeline.stages import align, annotate, dedup, qc, report, variant_call
from pipeline.stages import trim as trim_stage
from pipeline.utils.config import is_paired_end
from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)


def run_full_pipeline(config):
    """Run the full single-sample pipeline:
    QC -> [trim] -> index -> align -> [dedup] -> variant call -> [annotate] -> report.

    Returns a summary dict suitable for both the single-sample report and
    batch-mode aggregation.
    """
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_id = config.get("sample_id")
    threads = config.get("threads", 4)
    paired = is_paired_end(config)

    logger.info(f"Starting pipeline run{f' for sample {sample_id}' if sample_id else ''}")

    fastq_inputs = [config["fastq_r1"], config["fastq_r2"]] if paired else [config["fastq_input"]]

    qc_dir = output_dir / "qc"
    if not config.get("skip_qc"):
        if config.get("fastqc_enabled", True):
            qc.run_fastqc(fastq_inputs, qc_dir)
        qc_stats = qc.parse_fastq_basic(fastq_inputs[0])
    else:
        logger.info("Skipping QC stage (skip_qc=true)")
        qc_stats = {"reads": 0, "total_bases": 0, "avg_quality": 0, "reads_per_mb": 0}

    if config.get("trimming_enabled", True):
        trim_dir = output_dir / "trimmed"
        if paired:
            trimmed_r1, trimmed_r2 = trim_stage.trim_paired(
                config["fastq_r1"], config["fastq_r2"], trim_dir, threads=threads
            )
            align_kwargs = {"fastq_r1": trimmed_r1, "fastq_r2": trimmed_r2}
        else:
            trimmed = trim_stage.trim_single(config["fastq_input"], trim_dir, threads=threads)
            align_kwargs = {"fastq_file": trimmed}
    else:
        logger.info("Skipping trimming stage (trimming_enabled=false)")
        if paired:
            align_kwargs = {"fastq_r1": config["fastq_r1"], "fastq_r2": config["fastq_r2"]}
        else:
            align_kwargs = {"fastq_file": config["fastq_input"]}

    reference_fasta = config["reference_genome"]
    align.index_reference(reference_fasta)

    aligned_bam = output_dir / "aligned.bam"
    align.align_reads(reference_fasta, aligned_bam, threads=threads, **align_kwargs)

    if config.get("dedup_enabled", True):
        dedup_bam = output_dir / "dedup.bam"
        dedup.mark_duplicates(aligned_bam, dedup_bam, work_dir=output_dir / "_dedup_tmp")
        variant_input_bam = dedup_bam
    else:
        logger.info("Skipping duplicate-marking stage (dedup_enabled=false)")
        variant_input_bam = aligned_bam

    variants_vcf = output_dir / "variants.vcf.gz"
    variant_call.call_variants(variant_input_bam, reference_fasta, variants_vcf, min_depth=config.get("min_depth", 10))
    variant_count = variant_call.count_variants(variants_vcf)

    annotation_data = None
    if config.get("enable_annotation"):
        try:
            annotated_vcf = output_dir / "annotated.vcf.gz"
            annotate.annotate_variants(variants_vcf, annotated_vcf, genome_build=config.get("genome_build", "hg38"))
            annotation_data = annotate.parse_annotation(annotated_vcf, limit=50)
        except Exception as e:
            logger.warning(f"Annotation stage failed, continuing without it: {e}")

    report.generate_html_report(
        output_dir,
        qc_stats,
        variant_count,
        annotation_data=annotation_data,
        min_depth=config.get("min_depth", 10),
        sample_id=sample_id,
    )

    logger.info(f"Pipeline run complete{f' for sample {sample_id}' if sample_id else ''}")

    return {
        "sample_id": sample_id or "sample",
        "reads": qc_stats.get("reads", 0),
        "variant_count": variant_count,
        "status": "completed",
        "output_dir": str(output_dir),
    }


def run_batch_pipeline(sample_configs, output_dir):
    """Run the full pipeline for each sample config, then build a combined
    batch report linking to each sample's individual report."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for sample_config in sample_configs:
        sample_id = sample_config.get("sample_id", "sample")
        try:
            summary = run_full_pipeline(sample_config)
        except Exception as e:
            logger.error(f"Sample '{sample_id}' failed: {e}")
            summary = {
                "sample_id": sample_id,
                "reads": 0,
                "variant_count": 0,
                "status": f"failed: {e}",
                "output_dir": sample_config.get("output_dir", ""),
            }
        summaries.append(summary)

    report.generate_batch_report(output_dir, summaries)
    return summaries

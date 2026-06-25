# NGS Data Processing Pipeline

An end-to-end bioinformatics pipeline for processing Next-Generation
Sequencing (NGS) data: QC, trimming, alignment, duplicate marking, variant
calling, optional annotation, and HTML reporting — for single samples or
multi-sample batches.

This started as a from-scratch rebuild of a basic reference pipeline, with
the issues found during that review fixed (see [CHANGELOG.md](CHANGELOG.md)
for specifics): paired-end read support, real duplicate marking, a
depth-filter that's actually applied, no hardcoded genome build, no
binaries committed to git, and a hardened web UI.

## Pipeline stages

1. **QC** — FastQC + basic FASTQ stats (reads, bases, mean quality)
2. **Trimming** — adapter/quality trimming via `fastp` (toggleable)
3. **Alignment** — `bwa mem`, single- or paired-end, skips re-indexing an
   already-indexed reference
4. **Duplicate marking** — `samtools markdup` (toggleable)
5. **Variant calling** — `bcftools mpileup | bcftools call`, filtered by
   `min_depth`
6. **Annotation** *(optional)* — SnpEff, using the genome build from config;
   falls back to copying the VCF unchanged if SnpEff isn't installed
7. **Reporting** — self-contained HTML report per sample, plus a combined
   report for batch runs

## Install

Requires Python 3.8+ and, for real pipeline runs, the Linux tools:
`fastqc`, `bwa`, `samtools`, `bcftools`, `fastp`, `tabix` (and optionally
`snpEff`). These are Linux-only — on Windows, run them inside WSL2 or
Docker.

```bash
git clone <this-repo>
cd ngs-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements.txt

# Linux/WSL2:
sudo apt-get install -y fastqc bwa samtools bcftools fastp tabix
```

## Quick start

Generate small synthetic test data (no need to download a real genome):

```bash
python tools/generate_test_data.py data
```

Run a single sample:

```bash
ngs-pipeline run --config config/sample_config.yaml --output results/
```

Run a batch of samples from a sample sheet:

```bash
ngs-pipeline run-batch --config config/batch_config.yaml \
  --sample-sheet config/sample_sheet_example.csv --output results/
```

## Configuration

See `config/sample_config.yaml` for single-sample options and
`config/batch_config.yaml` + `config/sample_sheet_example.csv` for batch
mode. Key fields:

| Field | Meaning |
|---|---|
| `fastq_input` / `fastq_r1`+`fastq_r2` | Single-end or paired-end reads |
| `reference_genome` | Reference FASTA |
| `min_depth` | Variants below this depth are filtered out |
| `genome_build` | SnpEff genome DB to use if `enable_annotation: true` |
| `trimming_enabled` / `dedup_enabled` / `skip_qc` | Toggle pipeline stages |
| `align_tool` / `variant_caller` | Currently must be `bwa` / `bcftools` |

## Output

- `aligned.bam` — aligned reads (sorted, indexed)
- `dedup.bam` — duplicate-marked reads (if `dedup_enabled`)
- `variants.vcf.gz` — depth-filtered variant calls
- `annotated.vcf.gz` — annotated variants (if `enable_annotation`)
- `report.html` — per-sample summary report
- `batch_report.html` — combined report linking every sample (batch mode only)
- `qc/` — FastQC output

## Web UI

A small Flask app for submitting jobs through a browser instead of the CLI.
See [web/README.md](web/README.md) for setup, auth, and job storage details.

```bash
pip install -e ".[web]"
python -m web.app
```

## Docker

```bash
docker build -t ngs-pipeline:latest .
docker run -v $(pwd)/data:/app/data -v $(pwd)/results:/app/results ngs-pipeline:latest \
  run --config /app/config/sample_config.yaml --output /app/results/docker_run
# or:
docker-compose up
```

## Tests

```bash
pip install -e ".[dev]"
pytest -v --cov=pipeline
flake8 pipeline tools tests web
black --check -l 120 pipeline tools tests web
```

## License

MIT

# Changelog

This project began as a rebuild of a basic reference NGS pipeline
(FastQC → BWA-MEM → samtools/bcftools → optional SnpEff → HTML report,
plus a Flask job-submission UI). The review of that reference identified
the following gaps, all addressed in this version (`0.2.0`):

## 0.2.0

### Fixed
- **Paired-end reads were unsupported** — `align.py` only accepted a single
  FASTQ file. Added `fastq_r1`/`fastq_r2` support throughout config, sample
  sheet, alignment, and trimming.
- **Reference re-indexed on every run** — `bwa index` ran unconditionally
  even when index files already existed next to the reference. Now skipped
  if `reference_is_indexed()` finds all expected `.amb/.ann/.bwt/.pac/.sa`
  files.
- **`min_depth` config field was accepted but never applied** — variant
  calling now filters with `bcftools view -i 'DP>=min_depth'`.
- **Deprecated `samtools mpileup` variant-calling path** — switched to
  `bcftools mpileup | bcftools call`.
- **`align_tool` / `variant_caller` config fields were dead** — any value
  was accepted but silently ignored. Now validated against a supported set
  at config-load time.
- **SnpEff annotation hardcoded to `hg38`** regardless of the actual
  reference genome — now reads a `genome_build` config field.
- **`qc.py`'s FASTQ parser broke on `.fastq.gz`** despite the README
  documenting gzip input — now transparently handles both via `gzip.open`.
- **`logger.py` could attach duplicate `StreamHandler`s**, doubling log
  lines, if `setup_logger` was called more than once for the same name —
  now guarded with `if not logger.handlers`.
- **`requirements.txt` was missing `jinja2`** (used directly by
  `report.py`) and had drifted from `setup.py`'s `install_requires`.
- **Binary pipeline outputs and prebuilt BWA index files were committed to
  git** — `.gitignore` now excludes `results/`, `*.bam`, `*.vcf.gz`, and
  BWA index binaries; test data is generated on demand instead
  (`tools/generate_test_data.py`).

### Added
- **Read trimming stage** (`trim.py`) — `fastp`-based adapter/quality
  trimming, single- and paired-end, toggleable via `trimming_enabled`.
- **Duplicate-marking stage** (`dedup.py`) — `samtools markdup` following
  the sort→fixmate→sort→markdup workflow, toggleable via `dedup_enabled`.
- **Multi-sample/batch mode** — `ngs-pipeline run-batch --sample-sheet
  samples.csv` runs the full pipeline per row and produces a combined
  `batch_report.html` alongside each sample's own report.
- **Web UI hardening** — uploaded file extension/size validation, optional
  `X-API-Key` auth (`NGS_API_KEY` env var), and a SQLite-backed job store
  (`web/jobstore.py`) replacing the original in-memory dict that lost all
  job history on restart.
- **`tools/generate_test_data.py`** — deterministic synthetic
  reference + single/paired FASTQ generator for tests and manual
  verification, so no real genome download is needed.

## 0.1.0 (reference baseline)

Initial FastQC → BWA-MEM → samtools/bcftools → optional SnpEff → HTML
report pipeline with a basic Flask web UI.

# Agent Instructions — NGS Pipeline

This is a bioinformatics pipeline repo, not an automation/agent project —
but it follows the same separation-of-concerns spirit as the parent
workspace's WAT framework: deterministic Python stages do the actual work
(subprocess calls to fastqc/bwa/samtools/bcftools/fastp/snpEff), and the
CLI/web layer orchestrates them. Don't try to reimplement a bioinformatics
tool's logic in Python when the tool itself can be shelled out to.

## Architecture

```
pipeline/
  stages/        # one module per pipeline step, each independently testable
    qc.py         FastQC + FASTQ stat parsing (gzip-aware)
    trim.py       fastp adapter/quality trimming
    align.py      bwa index + bwa mem + samtools sort/index
    dedup.py      samtools sort -n -> fixmate -> sort -> markdup -> index
    variant_call.py   bcftools mpileup | bcftools call, then depth-filtered
    annotate.py   SnpEff annotation (genome build from config, not hardcoded)
    report.py     Jinja2 HTML report (per-sample + batch)
  utils/
    config.py     YAML config loading + validation (enums for align_tool/variant_caller)
    samplesheet.py  CSV sample-sheet parsing for batch mode
    logger.py     shared logger factory (idempotent handler attachment)
  workflows/
    full_pipeline.py  orchestrates the stage sequence per sample, and batch looping
  main.py         Click CLI: `run` (single sample) and `run-batch` (sample sheet)
web/              Flask job-submission UI (separate from the CLI, calls `ngs-pipeline` as a subprocess)
tools/
  generate_test_data.py  deterministic synthetic reference + FASTQ generator
```

Stage order: QC → trim → index → align → dedup → variant call → annotate → report.
Every stage after QC is individually toggleable via config
(`trimming_enabled`, `dedup_enabled`, `enable_annotation`, `skip_qc`).

## Config schema

See `pipeline/utils/config.py` `DEFAULTS` for the full field list. The two
load paths:
- `load_config(path)` — strict, for single-sample `run`: requires
  `reference_genome` + (`fastq_input` or `fastq_r1`+`fastq_r2`).
- `load_config(path, strict=False)` — for batch `run-batch`'s shared base
  config, where per-sample fields come from the CSV sample sheet instead
  (`pipeline/utils/samplesheet.py`).

`align_tool` and `variant_caller` are validated against
`SUPPORTED_ALIGN_TOOLS`/`SUPPORTED_VARIANT_CALLERS` in `config.py` — if you
add support for a new tool, add it there first or `load_config` will
reject it.

## Running things

```bash
# tests (mocked subprocess calls — no bioinformatics tools required)
pytest -v --cov=pipeline

# lint
flake8 pipeline tools tests web
black --check -l 120 pipeline tools tests web

# real end-to-end run (needs fastqc/bwa/samtools/bcftools/fastp on PATH —
# install via apt on Linux/WSL2, or use Docker)
python tools/generate_test_data.py data
ngs-pipeline run --config config/sample_config.yaml --output results/
ngs-pipeline run-batch --config config/batch_config.yaml --sample-sheet config/sample_sheet_example.csv --output results/

# web UI (run as a module, not `python web/app.py`, or the `web.jobstore` import fails)
python -m web.app
```

## Hard rules

- **Never commit pipeline outputs or binaries**: `results/`, `web_results/`,
  `uploads/`, `*.bam`, `*.vcf.gz`, BWA index files (`.amb/.ann/.bwt/.pac/.sa`).
  All of this is in `.gitignore` for a reason — the upstream reference repo
  committed exactly these and it bloated the repo. Test data is generated
  on demand via `tools/generate_test_data.py`, never checked in.
- **Secrets only in `.env`** (e.g. `NGS_API_KEY` for the web UI), never
  hardcoded. See `.env.example` for the documented keys.
- **Every new pipeline stage gets a test with mocked `subprocess.run`/`Popen`**
  (see `tests/test_dedup.py` or `tests/test_variant_call.py` for the
  pattern) — don't require real bwa/samtools to be installed just to run
  `pytest`.

## Self-improvement loop

When you hit a real-tool edge case the mocked tests didn't catch (e.g. a
new bcftools version changing flag behavior, fastp emitting an unexpected
report format), fix the stage module, add/extend its test to cover the
case, and add a line to `CHANGELOG.md` under an "Unreleased" or new version
heading. Don't silently patch around it — the changelog is what tells the
next person (or agent) why the code looks the way it does.

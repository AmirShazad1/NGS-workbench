import yaml

SUPPORTED_ALIGN_TOOLS = {"bwa"}
SUPPORTED_VARIANT_CALLERS = {"bcftools"}

REQUIRED_FIELDS = ("reference_genome", "output_dir")

DEFAULTS = {
    "fastq_input": "",
    "fastq_r1": "",
    "fastq_r2": "",
    "reference_genome": "",
    "output_dir": "./results",
    "threads": 4,
    "align_tool": "bwa",
    "variant_caller": "bcftools",
    "min_depth": 10,
    "genome_build": "hg38",
    "enable_annotation": False,
    "fastqc_enabled": True,
    "skip_qc": False,
    "trimming_enabled": True,
    "dedup_enabled": True,
}


def load_config(config_path, strict=True):
    """Load and validate a pipeline YAML config.

    A sample must provide either `fastq_input` (single-end) or both
    `fastq_r1`/`fastq_r2` (paired-end), plus `reference_genome` and
    `output_dir`. Pass `strict=False` for a batch base config, where
    `fastq_*`/`reference_genome` are supplied per-row by the sample sheet
    instead.
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}

    merged = {**DEFAULTS, **config}

    if strict:
        missing = [field for field in REQUIRED_FIELDS if not merged.get(field)]
        if missing:
            raise ValueError(f"Missing required config field(s): {', '.join(missing)}")

        has_single = bool(merged.get("fastq_input"))
        has_paired = bool(merged.get("fastq_r1")) and bool(merged.get("fastq_r2"))
        if not has_single and not has_paired:
            raise ValueError(
                "Config must provide 'fastq_input' (single-end) or both " "'fastq_r1' and 'fastq_r2' (paired-end)"
            )

    validate_choice("align_tool", merged["align_tool"], SUPPORTED_ALIGN_TOOLS)
    validate_choice("variant_caller", merged["variant_caller"], SUPPORTED_VARIANT_CALLERS)

    return merged


def validate_choice(field_name, value, supported):
    if value not in supported:
        raise ValueError(f"Unsupported {field_name} '{value}'. Supported: {sorted(supported)}")


def get_default_config():
    return dict(DEFAULTS)


def is_paired_end(config):
    return bool(config.get("fastq_r1")) and bool(config.get("fastq_r2"))

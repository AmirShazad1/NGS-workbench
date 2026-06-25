import csv
from pathlib import Path

REQUIRED_COLUMNS = ("sample_id",)


def load_sample_sheet(sample_sheet_path, base_config, output_dir):
    """Parse a CSV sample sheet into a list of per-sample configs.

    Each row must provide `sample_id` and either `fastq_input` or both
    `fastq_r1`/`fastq_r2`. Any column also present in `base_config` (e.g.
    `reference_genome`, `threads`) overrides the shared default for that
    sample only. Each sample's `output_dir` is namespaced under
    `output_dir/<sample_id>/`.
    """
    sample_sheet_path = Path(sample_sheet_path)
    with open(sample_sheet_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if any(v.strip() for v in row.values())]

    if not rows:
        raise ValueError(f"Sample sheet '{sample_sheet_path}' has no data rows")

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
    if missing_cols:
        raise ValueError(f"Sample sheet missing required column(s): {', '.join(missing_cols)}")

    sample_configs = []
    seen_ids = set()
    for i, row in enumerate(rows, start=2):  # header is line 1
        sample_id = row.get("sample_id", "").strip()
        if not sample_id:
            raise ValueError(f"Sample sheet row {i}: 'sample_id' is required")
        if sample_id in seen_ids:
            raise ValueError(f"Sample sheet has duplicate sample_id '{sample_id}'")
        seen_ids.add(sample_id)

        fastq_input = row.get("fastq_input", "").strip()
        fastq_r1 = row.get("fastq_r1", "").strip()
        fastq_r2 = row.get("fastq_r2", "").strip()
        if not fastq_input and not (fastq_r1 and fastq_r2):
            raise ValueError(
                f"Sample sheet row {i} ('{sample_id}'): provide 'fastq_input' " "or both 'fastq_r1' and 'fastq_r2'"
            )

        sample_config = dict(base_config)
        for key, value in row.items():
            if key == "sample_id" or value is None:
                continue
            value = value.strip()
            if value:
                sample_config[key] = value

        sample_config["fastq_input"] = fastq_input
        sample_config["fastq_r1"] = fastq_r1
        sample_config["fastq_r2"] = fastq_r2
        sample_config["sample_id"] = sample_id
        sample_config["output_dir"] = str(Path(output_dir) / sample_id)

        if not sample_config.get("reference_genome"):
            raise ValueError(
                f"Sample sheet row {i} ('{sample_id}'): 'reference_genome' must be set "
                "either in the base config or as a sample sheet column"
            )

        sample_configs.append(sample_config)

    return sample_configs

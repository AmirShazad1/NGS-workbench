import pytest
import yaml

from pipeline.utils.config import is_paired_end, load_config


def write_yaml(path, data):
    with open(path, "w") as f:
        yaml.dump(data, f)


def test_load_config_single_end(tmp_path):
    config_path = tmp_path / "config.yaml"
    write_yaml(
        config_path,
        {
            "fastq_input": "data/test.fastq",
            "reference_genome": "data/reference.fasta",
            "output_dir": "results/",
        },
    )
    config = load_config(config_path)
    assert config["fastq_input"] == "data/test.fastq"
    assert config["threads"] == 4
    assert not is_paired_end(config)


def test_load_config_paired_end(tmp_path):
    config_path = tmp_path / "config.yaml"
    write_yaml(
        config_path,
        {
            "fastq_r1": "data/R1.fastq",
            "fastq_r2": "data/R2.fastq",
            "reference_genome": "data/reference.fasta",
            "output_dir": "results/",
        },
    )
    config = load_config(config_path)
    assert is_paired_end(config)


def test_load_config_missing_reference_raises(tmp_path):
    config_path = tmp_path / "config.yaml"
    write_yaml(
        config_path,
        {
            "fastq_input": "data/test.fastq",
            "output_dir": "results/",
        },
    )
    with pytest.raises(ValueError, match="reference_genome"):
        load_config(config_path)


def test_load_config_missing_fastq_raises(tmp_path):
    config_path = tmp_path / "config.yaml"
    write_yaml(
        config_path,
        {
            "reference_genome": "data/reference.fasta",
            "output_dir": "results/",
        },
    )
    with pytest.raises(ValueError, match="fastq_input"):
        load_config(config_path)


def test_load_config_invalid_align_tool_raises(tmp_path):
    config_path = tmp_path / "config.yaml"
    write_yaml(
        config_path,
        {
            "fastq_input": "data/test.fastq",
            "reference_genome": "data/reference.fasta",
            "output_dir": "results/",
            "align_tool": "novoalign",
        },
    )
    with pytest.raises(ValueError, match="align_tool"):
        load_config(config_path)


def test_load_config_invalid_variant_caller_raises(tmp_path):
    config_path = tmp_path / "config.yaml"
    write_yaml(
        config_path,
        {
            "fastq_input": "data/test.fastq",
            "reference_genome": "data/reference.fasta",
            "output_dir": "results/",
            "variant_caller": "gatk",
        },
    )
    with pytest.raises(ValueError, match="variant_caller"):
        load_config(config_path)


def test_load_config_non_strict_allows_missing_fastq(tmp_path):
    config_path = tmp_path / "config.yaml"
    write_yaml(config_path, {"threads": 8})
    config = load_config(config_path, strict=False)
    assert config["threads"] == 8

"""Deterministic synthetic test data generator.

Produces a small reference FASTA and matching single-end/paired-end FASTQ
files so the pipeline can be exercised end-to-end without downloading real
genomic data. Always uses a fixed random seed, so output is reproducible.

Usage:
    python tools/generate_test_data.py [output_dir]
"""

import random
import sys
from pathlib import Path

SEED = 42
REFERENCE_LENGTH = 3000
READ_LENGTH = 100
NUM_READS = 200
MUTATION_RATE = 0.01
BASES = "ACGT"


def make_reference(rng, length=REFERENCE_LENGTH):
    return "".join(rng.choice(BASES) for _ in range(length))


def mutate(seq, rng, rate=MUTATION_RATE):
    bases = list(seq)
    for i in range(len(bases)):
        if rng.random() < rate:
            bases[i] = rng.choice(BASES)
    return "".join(bases)


def random_quality(rng, length, low=33, high=40):
    return "".join(chr(rng.randint(low, high) + 33) for _ in range(length))


def write_fasta(path, name, sequence):
    with open(path, "w") as f:
        f.write(f">{name}\n")
        for i in range(0, len(sequence), 70):
            f.write(sequence[i : i + 70] + "\n")


def write_fastq(path, reads):
    with open(path, "w") as f:
        for i, (seq, qual) in enumerate(reads):
            f.write(f"@read{i}\n{seq}\n+\n{qual}\n")


def generate_single_end_reads(reference, rng, num_reads=NUM_READS, read_length=READ_LENGTH):
    reads = []
    max_start = len(reference) - read_length
    for _ in range(num_reads):
        start = rng.randint(0, max_start)
        fragment = mutate(reference[start : start + read_length], rng)
        reads.append((fragment, random_quality(rng, read_length)))
    return reads


def generate_paired_end_reads(reference, rng, num_pairs=NUM_READS, read_length=READ_LENGTH, fragment_length=300):
    r1_reads, r2_reads = [], []
    max_start = len(reference) - fragment_length
    for _ in range(num_pairs):
        start = rng.randint(0, max_start)
        fragment = reference[start : start + fragment_length]
        r1 = mutate(fragment[:read_length], rng)
        r2_raw = fragment[-read_length:]
        r2 = mutate(_reverse_complement(r2_raw), rng)
        r1_reads.append((r1, random_quality(rng, read_length)))
        r2_reads.append((r2, random_quality(rng, read_length)))
    return r1_reads, r2_reads


def _reverse_complement(seq):
    complement = {"A": "T", "T": "A", "C": "G", "G": "C"}
    return "".join(complement[b] for b in reversed(seq))


def main(output_dir="data"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    reference = make_reference(rng)
    write_fasta(output_dir / "reference.fasta", "synthetic_chr1", reference)

    rng_se = random.Random(SEED)
    single_reads = generate_single_end_reads(reference, rng_se)
    write_fastq(output_dir / "test.fastq", single_reads)

    rng_pe = random.Random(SEED + 1)
    r1_reads, r2_reads = generate_paired_end_reads(reference, rng_pe)
    write_fastq(output_dir / "test_R1.fastq", r1_reads)
    write_fastq(output_dir / "test_R2.fastq", r2_reads)

    print(
        f"Wrote reference.fasta ({len(reference)} bp), test.fastq ({len(single_reads)} reads), "
        f"test_R1.fastq/test_R2.fastq ({len(r1_reads)} pairs) to {output_dir}"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")

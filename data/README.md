# Data directory

This directory is intentionally empty in version control. Pipeline inputs
(FASTQ/FASTA) and outputs (BAM/VCF/HTML) are never committed — they're
either your own real data or generated locally.

To generate small synthetic test data (a reference FASTA plus matching
single-end and paired-end FASTQ files):

```bash
python tools/generate_test_data.py data
```

This produces:
- `data/reference.fasta` — a 3kb synthetic reference sequence
- `data/test.fastq` — 200 single-end synthetic reads
- `data/test_R1.fastq` / `data/test_R2.fastq` — 200 paired-end synthetic reads

Generation is deterministic (fixed random seed), so re-running it always
produces identical output.

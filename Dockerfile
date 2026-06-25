FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    fastqc \
    bwa \
    samtools \
    bcftools \
    fastp \
    tabix \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel
RUN pip install -e .
RUN pip install -r requirements.txt

RUN mkdir -p /app/data /app/results

ENTRYPOINT ["ngs-pipeline"]
CMD ["run", "--help"]

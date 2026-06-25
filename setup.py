from setuptools import setup, find_packages

setup(
    name="ngs-pipeline",
    version="0.2.0",
    description="End-to-end NGS data processing pipeline (QC, trimming, alignment, dedup, variant calling, annotation, reporting)",
    packages=find_packages(include=["pipeline", "pipeline.*"]),
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1,<9",
        "pyyaml>=6.0,<7",
        "jinja2>=3.1,<4",
    ],
    extras_require={
        "dev": ["pytest>=7.4", "pytest-cov>=4.1", "flake8>=7.0", "black>=24.0"],
        "web": ["flask>=3.0,<4"],
    },
    entry_points={
        "console_scripts": [
            "ngs-pipeline=pipeline.main:cli",
        ],
    },
)

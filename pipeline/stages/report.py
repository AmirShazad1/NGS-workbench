import json
from pathlib import Path

from jinja2 import Template

from pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)

PIPELINE_VERSION = "0.2.0"

SAMPLE_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NGS Pipeline Report{% if sample_id %} - {{ sample_id }}{% endif %}</title>
<style>
  body { font-family: -apple-system, Arial, sans-serif; margin: 2rem; color: #222; }
  header { background: #1a1a2e; color: #fff; padding: 1.2rem 1.5rem; border-radius: 6px; }
  h1 { margin: 0; font-size: 1.4rem; }
  table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
  th, td { border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }
  tr:nth-child(even) { background: #f7f7f9; }
  .ok { color: #2e7d32; font-weight: bold; }
  .warn { color: #e65100; font-weight: bold; }
  pre { background: #f4f4f6; padding: 1rem; border-radius: 4px; overflow-x: auto; }
  section { margin-bottom: 1.5rem; }
</style>
</head>
<body>
<header><h1>NGS Pipeline Report{% if sample_id %} &mdash; {{ sample_id }}{% endif %}</h1></header>

<section>
  <h2>Summary</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Reads</td><td>{{ summary.reads }}</td></tr>
    <tr><td>Total bases</td><td>{{ summary.total_bases }}</td></tr>
    <tr><td>Average quality</td><td>{{ summary.avg_quality }}</td></tr>
    <tr><td>Variants called (min depth &ge; {{ summary.min_depth }})</td><td>{{ summary.variant_count }}</td></tr>
    <tr><td>Pipeline version</td><td>{{ summary.pipeline_version }}</td></tr>
  </table>
</section>

<section>
  <h2>Quality Control</h2>
  <pre>{{ qc_json }}</pre>
</section>

{% if annotation_data %}
<section>
  <h2>Annotated Variants (first {{ annotation_data|length }})</h2>
  <table>
    <tr><th>Chrom</th><th>Pos</th><th>Ref</th><th>Alt</th><th>Qual</th></tr>
    {% for v in annotation_data %}
    <tr><td>{{ v.chrom }}</td><td>{{ v.pos }}</td><td>{{ v.ref }}</td><td>{{ v.alt }}</td><td>{{ v.qual }}</td></tr>
    {% endfor %}
  </table>
</section>
{% endif %}

<section>
  <p class="ok">Pipeline completed successfully.</p>
</section>
</body>
</html>
"""

BATCH_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NGS Pipeline Batch Report</title>
<style>
  body { font-family: -apple-system, Arial, sans-serif; margin: 2rem; color: #222; }
  header { background: #1a1a2e; color: #fff; padding: 1.2rem 1.5rem; border-radius: 6px; }
  h1 { margin: 0; font-size: 1.4rem; }
  table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
  th, td { border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }
  tr:nth-child(even) { background: #f7f7f9; }
  a { color: #1a1a2e; }
</style>
</head>
<body>
<header><h1>NGS Pipeline Batch Report ({{ samples|length }} samples)</h1></header>
<table>
  <tr><th>Sample</th><th>Reads</th><th>Variants</th><th>Status</th><th>Report</th></tr>
  {% for s in samples %}
  <tr>
    <td>{{ s.sample_id }}</td>
    <td>{{ s.reads }}</td>
    <td>{{ s.variant_count }}</td>
    <td>{{ s.status }}</td>
    <td><a href="{{ s.sample_id }}/report.html">view</a></td>
  </tr>
  {% endfor %}
</table>
</body>
</html>
"""


def generate_html_report(output_dir, qc_stats, variant_count, annotation_data=None, min_depth=10, sample_id=None):
    output_dir = Path(output_dir)
    summary = {
        "reads": qc_stats.get("reads", 0),
        "total_bases": qc_stats.get("total_bases", 0),
        "avg_quality": qc_stats.get("avg_quality", 0),
        "variant_count": variant_count,
        "min_depth": min_depth,
        "pipeline_version": PIPELINE_VERSION,
    }

    template = Template(SAMPLE_REPORT_TEMPLATE)
    html = template.render(
        summary=summary,
        qc_json=json.dumps(qc_stats, indent=2),
        annotation_data=annotation_data,
        sample_id=sample_id,
    )

    report_path = output_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info(f"Report generated: {report_path}")
    return str(report_path)


def generate_batch_report(output_dir, sample_summaries):
    """Generate a combined index report linking each sample's own report.html.

    `sample_summaries` is a list of dicts with sample_id, reads, variant_count, status.
    """
    output_dir = Path(output_dir)
    template = Template(BATCH_REPORT_TEMPLATE)
    html = template.render(samples=sample_summaries)

    report_path = output_dir / "batch_report.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info(f"Batch report generated: {report_path}")
    return str(report_path)

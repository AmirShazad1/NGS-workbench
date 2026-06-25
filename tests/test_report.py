from pipeline.stages.report import generate_batch_report, generate_html_report


def test_generate_html_report_writes_file(tmp_path):
    qc_stats = {"reads": 100, "total_bases": 10000, "avg_quality": 35.2}
    path = generate_html_report(tmp_path, qc_stats, variant_count=5, min_depth=10, sample_id="sample1")

    content = (tmp_path / "report.html").read_text()
    assert path == str(tmp_path / "report.html")
    assert "sample1" in content
    assert "100" in content
    assert "5" in content


def test_generate_html_report_with_annotation_data(tmp_path):
    annotation_data = [{"chrom": "chr1", "pos": "100", "ref": "A", "alt": "G", "qual": "50"}]
    generate_html_report(tmp_path, {"reads": 1, "total_bases": 1, "avg_quality": 1}, 1, annotation_data=annotation_data)

    content = (tmp_path / "report.html").read_text()
    assert "chr1" in content


def test_generate_batch_report_links_each_sample(tmp_path):
    summaries = [
        {"sample_id": "s1", "reads": 10, "variant_count": 2, "status": "completed"},
        {"sample_id": "s2", "reads": 20, "variant_count": 3, "status": "completed"},
    ]
    path = generate_batch_report(tmp_path, summaries)

    content = (tmp_path / "batch_report.html").read_text()
    assert path == str(tmp_path / "batch_report.html")
    assert "s1/report.html" in content
    assert "s2/report.html" in content

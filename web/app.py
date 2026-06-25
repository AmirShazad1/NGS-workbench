import os
import shutil
import subprocess
import sys
import threading
import uuid
import zipfile
from pathlib import Path

import yaml
from flask import Flask, jsonify, render_template, request, send_file

from web.jobstore import JobStore

APP_DIR = Path(__file__).parent.parent
RESULTS_FOLDER = APP_DIR / "web_results"
UPLOAD_FOLDER = APP_DIR / "uploads"
DB_PATH = APP_DIR / "web_results" / "jobs.db"
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)

ALLOWED_FASTQ_SUFFIXES = (".fastq", ".fastq.gz", ".fq", ".fq.gz")
ALLOWED_REFERENCE_SUFFIXES = (".fasta", ".fa", ".fasta.gz", ".fa.gz")
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500MB

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

jobs = JobStore(DB_PATH)

API_KEY = os.environ.get("NGS_API_KEY", "").strip()


@app.before_request
def check_api_key():
    if not API_KEY:
        return None  # auth disabled when no key is configured (local/dev use)
    if request.endpoint == "index" or (request.path.startswith("/static")):
        return None
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401


def _has_allowed_suffix(filename, allowed_suffixes):
    name = filename.lower()
    return any(name.endswith(suffix) for suffix in allowed_suffixes)


def run_pipeline_job(job_id, fastq_file, reference_file, config):
    output_dir = RESULTS_FOLDER / job_id
    jobs.update_job(job_id, status="running", started_at=_now())
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        job_fastq = output_dir / Path(fastq_file).name
        job_ref = output_dir / Path(reference_file).name
        shutil.copy(fastq_file, job_fastq)
        shutil.copy(reference_file, job_ref)

        config["fastq_input"] = str(job_fastq)
        config["reference_genome"] = str(job_ref)
        config["output_dir"] = str(output_dir)
        config_file = output_dir / "pipeline_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        # Use the current interpreter + module invocation rather than the bare
        # `ngs-pipeline` console script, which only resolves if the venv is
        # activated on PATH (it isn't, when this process is launched directly
        # via its full venv python path).
        cmd = [
            sys.executable,
            "-m",
            "pipeline.main",
            "run",
            "--config",
            str(config_file),
            "--output",
            str(output_dir),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=str(APP_DIR))

        if result.returncode == 0:
            jobs.update_job(job_id, status="completed", progress=100)
        else:
            jobs.update_job(job_id, status="failed", error=(result.stderr or "Unknown error")[-2000:])
    except subprocess.TimeoutExpired:
        jobs.update_job(job_id, status="failed", error="Pipeline timed out")
    except Exception as e:
        jobs.update_job(job_id, status="failed", error=str(e))
    finally:
        jobs.update_job(job_id, completed_at=_now())


def _now():
    from datetime import datetime

    return datetime.now().isoformat()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/job", methods=["POST"])
def create_job():
    try:
        if "fastq" not in request.files or "reference" not in request.files:
            return jsonify({"error": "Missing files"}), 400
        fastq_file = request.files["fastq"]
        reference_file = request.files["reference"]
        if not fastq_file.filename or not reference_file.filename:
            return jsonify({"error": "Empty filename"}), 400

        if not _has_allowed_suffix(fastq_file.filename, ALLOWED_FASTQ_SUFFIXES):
            return jsonify({"error": f"FASTQ file must end in one of {ALLOWED_FASTQ_SUFFIXES}"}), 400
        if not _has_allowed_suffix(reference_file.filename, ALLOWED_REFERENCE_SUFFIXES):
            return jsonify({"error": f"Reference file must end in one of {ALLOWED_REFERENCE_SUFFIXES}"}), 400

        job_id = str(uuid.uuid4())[:8]
        fastq_path = UPLOAD_FOLDER / f"{job_id}_{Path(fastq_file.filename).name}"
        ref_path = UPLOAD_FOLDER / f"{job_id}_{Path(reference_file.filename).name}"
        fastq_file.save(fastq_path)
        reference_file.save(ref_path)

        try:
            threads = int(request.form.get("threads", 4))
        except ValueError:
            threads = 4
        config = {
            "threads": max(1, min(threads, 32)),
            "enable_annotation": request.form.get("enable_annotation") == "on",
            "fastqc_enabled": True,
        }

        jobs.create_job(job_id, RESULTS_FOLDER / job_id)
        t = threading.Thread(target=run_pipeline_job, args=(job_id, str(fastq_path), str(ref_path), config))
        t.daemon = True
        t.start()
        return jsonify({"job_id": job_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    return jsonify(jobs.list_jobs())


@app.route("/api/job/<job_id>", methods=["GET"])
def get_job(job_id):
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/job/<job_id>/error", methods=["GET"])
def get_job_error(job_id):
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"job_id": job_id, "status": job["status"], "error": job["error"]})


@app.route("/api/job/<job_id>/report")
def get_report(job_id):
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    report = Path(job["output_dir"]) / "report.html"
    if not report.exists():
        return jsonify({"error": "Report not generated"}), 404
    return send_file(report, as_attachment=True)


@app.route("/api/job/<job_id>/download")
def download_results(job_id):
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    output_dir = Path(job["output_dir"])
    if not output_dir.exists():
        return jsonify({"error": "No results folder"}), 404

    zip_path = RESULTS_FOLDER / f"{job_id}_results.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        files_added = 0
        for f in output_dir.rglob("*"):
            if f.is_file():
                zf.write(f, arcname=f.relative_to(output_dir))
                files_added += 1
    if files_added == 0:
        zip_path.unlink(missing_ok=True)
        return jsonify({"error": "No output files generated"}), 404
    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)

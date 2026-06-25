async function submitJob(event) {
  event.preventDefault();
  const form = document.getElementById("job-form");
  const status = document.getElementById("submit-status");
  const formData = new FormData(form);

  status.textContent = "Submitting...";
  try {
    const response = await fetch("/api/job", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) {
      status.textContent = `Error: ${data.error || "submission failed"}`;
      return;
    }
    status.textContent = `Job submitted: ${data.job_id}`;
    form.reset();
    loadJobs();
  } catch (err) {
    status.textContent = `Error: ${err}`;
  }
}

async function loadJobs() {
  const tbody = document.querySelector("#jobs-table tbody");
  try {
    const response = await fetch("/api/jobs");
    const jobs = await response.json();
    tbody.innerHTML = "";
    for (const job of jobs) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${job.job_id}</td>
        <td class="status-${job.status}">${job.status}</td>
        <td>${job.created_at || ""}</td>
        <td>
          <a href="/api/job/${job.job_id}/report" target="_blank">report</a> |
          <a href="/api/job/${job.job_id}/download">download</a>
        </td>`;
      tbody.appendChild(row);
    }
  } catch (err) {
    console.error("Failed to load jobs", err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("job-form").addEventListener("submit", submitJob);
  loadJobs();
  setInterval(loadJobs, 5000);
});

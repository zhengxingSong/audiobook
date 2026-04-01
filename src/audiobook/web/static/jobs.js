function $(id) {
  return document.getElementById(id);
}

function renderJobCard(job) {
  const percent = job.total_blocks ? Math.round((job.processed_blocks / job.total_blocks) * 100) : 0;
  return `
    <article class="service-card">
      <header>
        <div>
          <h3>${job.novel_name}</h3>
          <p>${job.job_id}</p>
        </div>
        <span class="status-badge">${job.status}</span>
      </header>
      <p>Stage: ${job.current_stage || "Queued"}</p>
      <p>Blocks: ${job.processed_blocks}/${job.total_blocks}</p>
      <div class="progress-track"><div class="progress-fill" style="width: ${percent}%"></div></div>
      <footer>
        <a class="button button-secondary" href="/jobs/${job.job_id}">Open detail</a>
      </footer>
    </article>
  `;
}

async function refreshJobs() {
  const response = await fetch("/api/jobs");
  const data = await response.json();
  const container = $("jobs-table");
  if (!data.jobs.length) {
    container.innerHTML = '<article class="service-card"><h3>No jobs yet</h3><p>Submit a file or path to create the first conversion run.</p></article>';
    return;
  }
  container.innerHTML = data.jobs.map(renderJobCard).join("");
}

async function submitJob(event) {
  event.preventDefault();
  const status = $("job-form-status");
  const form = event.currentTarget;
  const formData = new FormData(form);
  status.textContent = "Submitting job...";

  const response = await fetch("/api/jobs", {
    method: "POST",
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    status.textContent = payload.detail || "Failed to submit job.";
    return;
  }

  status.textContent = `Job ${payload.job_id} created.`;
  form.reset();
  form.querySelector('input[name="tts_endpoint"]').value = "demo://tone";
  await refreshJobs();
}

document.addEventListener("DOMContentLoaded", () => {
  $("job-form")?.addEventListener("submit", submitJob);
  $("jobs-refresh")?.addEventListener("click", refreshJobs);
  refreshJobs();
  window.setInterval(refreshJobs, 4000);
});

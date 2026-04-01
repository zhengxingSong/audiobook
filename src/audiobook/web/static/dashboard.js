const state = {
  jobs: [],
  selectedJobId: null,
};

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const node = byId(id);
  if (node) {
    node.textContent = value;
  }
}

function summarizeJobs(jobs) {
  const active = jobs.length;
  const processed = jobs.reduce(
    (sum, job) => sum + (job.processed_fragments || job.processed_blocks || 0),
    0
  );
  const failed = jobs.reduce((sum, job) => sum + (job.failed_fragments || 0), 0);

  setText("job-count", String(active));
  setText("job-summary", active ? `${active} live conversion lanes visible` : "No registered jobs yet");
  setText("metric-active", String(active));
  setText("metric-fragments", String(processed));
  setText("metric-failed", String(failed));
}

function renderInspector(job) {
  if (!job) {
    setText("detail-title", "Awaiting job selection");
    setText("detail-text", "Select a live job card to inspect its stage, chapter progress, and failure counts.");
    setText("detail-stage", "Idle");
    setText("detail-progress", "0%");
    setText("detail-failed", "0");
    setText("detail-id", "No selection");
    return;
  }

  setText("detail-title", job.novel_name || "Unnamed job");
  setText("detail-text", "This job is currently visible to the control room. Track its stage, progress, and failures here while the API continues updating in the background.");
  setText("detail-stage", job.current_stage || "Unknown");
  setText("detail-progress", `${job.percent_complete || 0}%`);
  setText("detail-failed", String(job.failed_fragments || 0));
  setText("detail-id", job.job_id);
}

function jobCard(job) {
  const percent =
    job.percent_complete ??
    (job.total_blocks ? Math.round((job.processed_blocks / job.total_blocks) * 100) : 0);
  const processed = job.processed_fragments || job.processed_blocks || 0;
  const total = job.total_fragments || job.total_blocks || 0;
  const selected = state.selectedJobId === job.job_id;
  return `
    <article class="job-card ${selected ? "is-selected" : ""}" data-job-id="${job.job_id}">
      <div class="job-card-header">
        <div>
          <h3>${job.novel_name || "Untitled conversion"}</h3>
          <div class="job-id">${job.job_id}</div>
        </div>
        <span class="stage-pill">${job.current_stage || "Idle"}</span>
      </div>
      <div class="job-meta">
        <div><span>Progress</span><strong>${percent}%</strong></div>
        <div><span>Processed</span><strong>${processed}/${total}</strong></div>
        <div><span>Failures</span><strong>${job.failed_fragments || 0}</strong></div>
      </div>
      <div class="progress-track" aria-hidden="true">
        <div class="progress-fill" style="width: ${percent}%"></div>
      </div>
    </article>
  `;
}

function bindJobSelection() {
  document.querySelectorAll(".job-card").forEach((node) => {
    node.addEventListener("click", () => {
      state.selectedJobId = node.dataset.jobId;
      renderJobs(state.jobs);
    });
  });
}

function renderJobs(jobs) {
  const container = byId("jobs-container");
  if (!container) {
    return;
  }

  if (!jobs.length) {
    container.innerHTML = `
      <article class="empty-state">
        <span class="empty-badge">Standby</span>
        <h3>No active jobs registered</h3>
        <p>The page is live and connected. Once a conversion tracker is registered, job cards will appear here with completion, stage, and failure telemetry.</p>
      </article>
    `;
    renderInspector(null);
    return;
  }

  if (!state.selectedJobId || !jobs.some((job) => job.job_id === state.selectedJobId)) {
    state.selectedJobId = jobs[0].job_id;
  }

  container.innerHTML = jobs.map(jobCard).join("");
  bindJobSelection();

  const selected = jobs.find((job) => job.job_id === state.selectedJobId) || jobs[0];
  renderInspector(selected);
}

async function refreshHealth() {
  const response = await fetch("/health");
  const data = await response.json();
  setText("health-status", data.status === "ok" ? "Healthy" : "Attention");
  setText("health-meta", `${data.active_jobs} active job${data.active_jobs === 1 ? "" : "s"} visible on the service`);
}

async function refreshJobs() {
  const response = await fetch("/api/jobs");
  const data = await response.json();
  state.jobs = data.jobs || [];
  summarizeJobs(state.jobs);
  renderJobs(state.jobs);
}

async function refreshAll() {
  try {
    await Promise.all([refreshHealth(), refreshJobs()]);
  } catch (error) {
    setText("health-status", "Degraded");
    setText("health-meta", "Unable to load service telemetry");
    console.error(error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  byId("refresh-button")?.addEventListener("click", refreshAll);
  refreshAll();
  window.setInterval(refreshAll, 5000);
});

function detailNode(id) {
  return document.getElementById(id);
}

async function loadJob() {
  const jobId = window.JOB_ID;
  const response = await fetch(`/api/jobs/${jobId}`);
  const payload = await response.json();

  if (!response.ok) {
    detailNode("job-status-title").textContent = "Job not found";
    detailNode("job-errors-preview").textContent = JSON.stringify(payload, null, 2);
    return;
  }

  const percent = payload.total_blocks ? Math.round((payload.processed_blocks / payload.total_blocks) * 100) : 0;
  detailNode("detail-page-title").textContent = payload.novel_name;
  detailNode("job-status-title").textContent = payload.novel_name;
  detailNode("job-status").textContent = payload.status;
  detailNode("job-stage").textContent = payload.current_stage || "Queued";
  detailNode("job-blocks").textContent = `${payload.processed_blocks}/${payload.total_blocks}`;
  detailNode("job-fragments").textContent = `${payload.total_fragments}`;
  detailNode("job-progress-fill").style.width = `${percent}%`;
  detailNode("job-progress-text").textContent = `${percent}% complete`;
  detailNode("job-report-link").href = `/api/jobs/${jobId}/report`;
  detailNode("job-errors-link").href = `/api/jobs/${jobId}/errors`;
  detailNode("job-result-link").href = `/api/jobs/${jobId}/result`;

  const errorsResponse = await fetch(`/api/jobs/${jobId}/errors`);
  const errorsPayload = await errorsResponse.json();
  detailNode("job-errors-preview").textContent = JSON.stringify(errorsPayload, null, 2);
}

document.addEventListener("DOMContentLoaded", () => {
  loadJob();
  window.setInterval(loadJob, 4000);
});

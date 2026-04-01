function voiceNode(id) {
  return document.getElementById(id);
}

function renderVoiceCard(voice) {
  return `
    <article class="service-card">
      <header>
        <div>
          <h3>${voice.name}</h3>
          <p>${voice.voice_id}</p>
        </div>
        <span class="status-badge">${voice.gender} / ${voice.age_range}</span>
      </header>
      <p>${voice.description || "No description provided."}</p>
      <p>Tags: ${(voice.tags || []).join(", ") || "none"}</p>
      <footer>
        <button class="button button-secondary" data-delete-voice="${voice.voice_id}" type="button">Delete</button>
      </footer>
    </article>
  `;
}

async function refreshVoices() {
  const response = await fetch("/api/voices");
  const payload = await response.json();
  const container = voiceNode("voices-table");
  if (!payload.voices.length) {
    container.innerHTML = '<article class="service-card"><h3>No voices stored</h3><p>Upload a reference sample to seed the voice library.</p></article>';
    return;
  }
  container.innerHTML = payload.voices.map(renderVoiceCard).join("");
  document.querySelectorAll("[data-delete-voice]").forEach((button) => {
    button.addEventListener("click", async () => {
      await fetch(`/api/voices/${button.dataset.deleteVoice}`, { method: "DELETE" });
      await refreshVoices();
    });
  });
}

async function submitVoice(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const status = voiceNode("voice-form-status");
  status.textContent = "Uploading voice...";

  const response = await fetch("/api/voices", {
    method: "POST",
    body: new FormData(form),
  });
  const payload = await response.json();
  if (!response.ok) {
    status.textContent = payload.detail || "Failed to add voice.";
    return;
  }
  status.textContent = `Voice ${payload.name} added.`;
  form.reset();
  await refreshVoices();
}

document.addEventListener("DOMContentLoaded", () => {
  voiceNode("voice-form")?.addEventListener("submit", submitVoice);
  voiceNode("voices-refresh")?.addEventListener("click", refreshVoices);
  refreshVoices();
});

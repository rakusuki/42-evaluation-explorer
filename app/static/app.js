function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function getJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  const data = await response.json();
  return { response, data };
}

function errorBox(data) {
  return `<div class="notice error"><strong>${escapeHtml(data.status_code || "Error")}</strong> ${escapeHtml(data.message || "Request failed")}</div>`;
}

function renderProgress(items) {
  if (!items.length) return '<p class="muted">No matching project progress found.</p>';
  const rows = items.map((item) => `
    <tr>
      <td>${escapeHtml(item.project_name)}</td>
      <td>${escapeHtml(item.project_id)}</td>
      <td>${escapeHtml(item.status)}</td>
      <td>${escapeHtml(item.final_mark)}</td>
      <td>${escapeHtml(item.validated)}</td>
    </tr>`).join("");
  return `<table><thead><tr><th>Project</th><th>ID</th><th>Status</th><th>Mark</th><th>Validated</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderReviews(items) {
  if (!items.length) return '<p class="muted">No review records were visible to this token.</p>';
  const rows = items.map((item) => `
    <tr>
      <td>${escapeHtml(item.id)}</td>
      <td>${escapeHtml(item.project_id)}</td>
      <td>${escapeHtml(item.final_mark)}</td>
      <td>${escapeHtml(item.corrector)}</td>
      <td>${escapeHtml(item.begin_at)}</td>
      <td class="comment">${escapeHtml(item.comment)}</td>
    </tr>`).join("");
  return `<table><thead><tr><th>ID</th><th>Project</th><th>Mark</th><th>Corrector</th><th>Date</th><th>Comment</th></tr></thead><tbody>${rows}</tbody></table>`;
}

document.querySelector("#progress-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const login = document.querySelector("#login").value.trim();
  const project = document.querySelector("#project").value.trim();
  const status = document.querySelector("#status").value;
  const params = new URLSearchParams();
  if (project) params.set("project", project);
  if (status) params.set("status", status);
  const target = document.querySelector("#progress-result");
  target.innerHTML = "Loading...";
  try {
    const { data } = await getJson(`/api/users/${encodeURIComponent(login)}/project-progress?${params}`);
    target.innerHTML = data.ok ? renderProgress(data.items || []) : errorBox(data);
  } catch (error) {
    target.innerHTML = `<div class="notice error">${escapeHtml(error)}</div>`;
  }
});

document.querySelector("#review-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const login = document.querySelector("#review-login").value.trim();
  const projectId = document.querySelector("#review-project-id").value.trim();
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  const target = document.querySelector("#review-result");
  target.innerHTML = "Loading...";
  try {
    const { data } = await getJson(`/api/reviews/${encodeURIComponent(login)}?${params}`);
    target.innerHTML = data.ok ? renderReviews(data.items || []) : errorBox(data);
  } catch (error) {
    target.innerHTML = `<div class="notice error">${escapeHtml(error)}</div>`;
  }
});

document.querySelector("#probe-button").addEventListener("click", async () => {
  const resource = document.querySelector("#probe-resource").value;
  const value = document.querySelector("#probe-value").value.trim();
  const target = document.querySelector("#probe-result");
  if (!value) {
    target.textContent = "Enter a login, project ID, or slug.";
    return;
  }
  target.textContent = "Loading...";
  const params = new URLSearchParams({ resource, value });
  try {
    const { data } = await getJson(`/api/test/raw?${params}`);
    target.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    target.textContent = String(error);
  }
});

document.querySelectorAll("button[data-probe]").forEach((button) => {
  button.addEventListener("click", async () => {
    const kind = button.dataset.probe;
    const scaleTeamId = document.querySelector("#scale-team-id").value.trim();
    const teamId = document.querySelector("#team-id").value.trim();
    let url;
    if (kind === "scale-team" && scaleTeamId) url = `/api/test/scale-teams/${scaleTeamId}`;
    if (kind === "feedbacks" && scaleTeamId) url = `/api/test/scale-teams/${scaleTeamId}/feedbacks`;
    if (kind === "uploads" && teamId) url = `/api/test/teams/${teamId}/uploads`;
    const target = document.querySelector("#id-probe-result");
    if (!url) {
      target.textContent = "Enter the required ID.";
      return;
    }
    target.textContent = "Loading...";
    try {
      const { data } = await getJson(url);
      target.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      target.textContent = String(error);
    }
  });
});

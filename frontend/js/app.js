const API_BASE = 'https://complaint-detection.onrender.com';

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    const err = new Error(errBody.detail || `POST ${path} failed: ${res.status}`);
    err.status = res.status;
    err.detail = errBody.detail;
    throw err;
  }
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`DELETE ${path} failed: ${res.status}`);
  return res.json();
}

function showNotification(message, type = 'info') {
  const el = document.createElement('div');
  el.className = `notification ${type}`;
  el.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-info-circle'}"></i> ${message}`;
  document.body.appendChild(el);
  setTimeout(() => { el.remove(); }, 3500);
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function sentimentTag(s) {
  const map = { positive: 'tag-positive', negative: 'tag-negative', neutral: 'tag-neutral' };
  return `<span class="tag ${map[s] || 'tag-neutral'}">${s}</span>`;
}

function priorityTag(p) {
  const map = { high: 'tag-high', medium: 'tag-medium', low: 'tag-low' };
  return `<span class="tag ${map[p] || 'tag-low'}">${p}</span>`;
}

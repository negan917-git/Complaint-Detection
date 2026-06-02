const API_BASE = 'https://complaint-detection.onrender.com';

function getToken() {
  return localStorage.getItem('token');
}

function getAuthHeaders() {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, { headers: getAuthHeaders() });
  if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
  let data;
  try { data = await res.json(); } catch { throw new Error(`Ошибка ответа от ${path}`); }
  if (!res.ok) throw new Error(data.detail || `GET ${path} failed: ${res.status}`);
  return data;
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
  let data;
  try { data = await res.json(); } catch { throw new Error(`Ошибка ответа от ${path}`); }
  if (!res.ok) {
    const err = new Error(data.detail || `POST ${path} failed: ${res.status}`);
    err.status = res.status;
    err.detail = data.detail;
    throw err;
  }
  return data;
}

async function apiDelete(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
  let data;
  try { data = await res.json(); } catch { throw new Error(`Ошибка ответа от ${path}`); }
  if (!res.ok) throw new Error(data.detail || `DELETE ${path} failed: ${res.status}`);
  return data;
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

const CATEGORY_LABELS = {
  general: 'Общее',
  technical: 'Техническое',
  billing: 'Оплата',
  product: 'Продукт',
  account: 'Аккаунт',
  service: 'Сервис',
  support: 'Поддержка',
};

const EMOTION_LABELS = {
  happy: 'Счастлив',
  angry: 'Злой',
  frustrated: 'Раздражён',
  confused: 'Смущён',
  neutral: 'Нейтрально',
};

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

function sentimentTag(s) {
  const map = { positive: 'tag-positive', negative: 'tag-negative', neutral: 'tag-neutral' };
  return `<span class="tag ${map[s] || 'tag-neutral'}">${capitalize(s)}</span>`;
}

function priorityTag(p) {
  const map = { high: 'tag-high', medium: 'tag-medium', low: 'tag-low' };
  return `<span class="tag ${map[p] || 'tag-low'}">${capitalize(p)}</span>`;
}

function checkAuth() {
  if (!getToken()) {
    window.location.href = 'login.html';
  }
}

function logout() {
  localStorage.removeItem('token');
  window.location.href = 'login.html';
}

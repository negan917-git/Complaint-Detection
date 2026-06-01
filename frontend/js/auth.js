const API_BASE = 'https://complaint-detection.onrender.com';

function getToken() {
  return localStorage.getItem('token');
}

function setToken(token) {
  localStorage.setItem('token', token);
}

function removeToken() {
  localStorage.removeItem('token');
}

function getAuthHeaders() {
  const token = getToken();
  return token ? { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` } : { 'Content-Type': 'application/json' };
}

async function apiPostAuth(path, body) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error('Не удалось подключиться к серверу. Проверьте, запущен ли backend.');
  }
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Ошибка запроса');
  }
  return data;
}

function showAuthError(message) {
  const el = document.getElementById('authError');
  el.textContent = message;
  el.classList.add('visible');
}

function hideAuthError() {
  const el = document.getElementById('authError');
  el.classList.remove('visible');
}

function switchTab(tab) {
  hideAuthError();
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  document.querySelectorAll('.auth-form').forEach(f => f.classList.toggle('active', f.id === tab + 'Form'));
}

async function handleLogin(e) {
  e.preventDefault();
  hideAuthError();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  if (!email) { showAuthError('Введите email'); return; }
  if (!password || password.length < 6) { showAuthError('Пароль должен быть минимум 6 символов'); return; }
  const btn = document.getElementById('loginBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Вход...';
  try {
    const data = await apiPostAuth('/api/auth/login', { email, password });
    setToken(data.access_token);
    window.location.href = 'index.html';
  } catch (err) {
    showAuthError(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Войти';
  }
}

async function handleRegister(e) {
  e.preventDefault();
  hideAuthError();
  const username = document.getElementById('regUsername').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value;
  if (!username) { showAuthError('Введите имя пользователя'); return; }
  if (!email) { showAuthError('Введите email'); return; }
  if (!password || password.length < 6) { showAuthError('Пароль должен быть минимум 6 символов'); return; }
  const btn = document.getElementById('registerBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Регистрация...';
  try {
    await apiPostAuth('/api/auth/register', { username, email, password });
    const loginData = await apiPostAuth('/api/auth/login', { email, password });
    setToken(loginData.access_token);
    window.location.href = 'index.html';
  } catch (err) {
    showAuthError(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-user-plus"></i> Зарегистрироваться';
  }
}

function logout() {
  removeToken();
  window.location.href = 'login.html';
}

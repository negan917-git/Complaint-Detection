let deletingBotId = null;

async function loadBots() {
  const grid = document.getElementById('botGrid');
  try {
    const bots = await apiGet('/api/bots');
    if (bots.length === 0) {
      grid.innerHTML = '<div class="empty-state"><i class="fas fa-robot"></i><p>Нет подключённых ботов</p></div>';
      return;
    }
    grid.innerHTML = bots.map(b => `
      <div class="bot-card">
        <div class="bot-header">
          <div class="bot-avatar"><i class="fas fa-robot"></i></div>
          <div>
            <div class="bot-name">${b.name}</div>
            <div class="bot-username">@${b.username}</div>
          </div>
        </div>
        <div class="bot-stats">
          <div class="bot-stat">
            <strong>${b.messages_count}</strong>
            сообщений
          </div>
          <div class="bot-stat">
            <span class="tag-status connected"><span class="dot"></span> ${b.status}</span>
          </div>
        </div>
        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">
          ID: ${b.telegram_bot_id || '—'} &middot; Подключён: ${formatDate(b.created_at)}
        </div>
        <div class="bot-actions">
          <button class="btn btn-primary btn-sm" onclick="syncBot(${b.id}, event)">
            <i class="fas fa-sync"></i> Sync Messages
          </button>
          <button class="btn btn-danger btn-sm" onclick="showDeleteBotModal(${b.id})">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    grid.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.detail || e.message || 'Ошибка загрузки ботов'}</p></div>`;
  }
}

async function syncBot(id, event) {
  const targetBtn = event?.target?.closest?.('.btn');
  const originalHtml = targetBtn?.innerHTML || '';
  if (targetBtn) targetBtn.innerHTML = '<span class="spinner"></span> Синхронизация...';
  try {
    const res = await apiPost(`/api/bots/${id}/sync`);
    showNotification(`Синхронизировано ${res.messages_synced} сообщений`, 'success');
    loadBots();
  } catch (e) {
    showNotification(e.detail || e.message || 'Ошибка синхронизации', 'error');
    if (targetBtn) targetBtn.innerHTML = originalHtml;
  }
}

function showDeleteBotModal(id) {
  deletingBotId = id;
  document.getElementById('deleteBotModal').style.display = 'flex';
}

function hideDeleteBotModal() {
  document.getElementById('deleteBotModal').style.display = 'none';
  deletingBotId = null;
}

async function confirmDeleteBot() {
  if (!deletingBotId) return;
  try {
    await apiDelete(`/api/bots/${deletingBotId}`);
    showNotification('Бот удалён', 'success');
    hideDeleteBotModal();
    loadBots();
  } catch (e) {
    showNotification(e.detail || e.message || 'Ошибка удаления', 'error');
  }
}

function showConnectBotModal() {
  document.getElementById('connectBotModal').style.display = 'flex';
}

function hideConnectBotModal() {
  document.getElementById('connectBotModal').style.display = 'none';
  document.getElementById('botToken').value = '';
}

async function connectBot() {
  const token = document.getElementById('botToken').value.trim();
  if (!token) {
    showNotification('Введите токен Telegram-бота', 'error');
    return;
  }
  const btn = document.querySelector('#connectBotModal .btn-primary');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Подключение...';
  try {
    await apiPost('/api/bots/connect', { token });
    showNotification('Бот успешно подключён', 'success');
    hideConnectBotModal();
    loadBots();
  } catch (e) {
    showNotification(e.detail || e.message || 'Ошибка подключения бота', 'error');
  }
  btn.disabled = false;
  btn.innerHTML = '<i class="fas fa-plus"></i> Подключить';
}

document.addEventListener('DOMContentLoaded', loadBots);

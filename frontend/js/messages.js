function AISummaryCard(summary) {
  if (!summary) return '';
  return `
    <div class="ai-summary">
      <div class="ai-header">
        <span class="ai-icon">🤖</span>
        Резюме AI
      </div>
      <div class="ai-text">${summary}</div>
    </div>
  `;
}

function MessageCard(m) {
  const sentimentBadge = sentimentTag(m.sentiment);
  const priorityBadge = priorityTag(m.priority);
  const complaintBadge = m.complaint
    ? '<span class="tag tag-complaint">Жалоба</span>'
    : '';
  const usernameHtml = m.username
    ? `<span class="username-muted">@${m.username}</span>`
    : '';

  return `
    <div class="message-card">
      <div class="card-top">
        <span class="user-name">
          ${m.name || 'Аноним'}
          ${usernameHtml}
        </span>
        <span class="date" title="${m.created_at ? new Date(m.created_at).toLocaleString('ru-RU') : ''}">${m.created_at ? formatDate(m.created_at) : '—'}</span>
        <div class="badges">
          ${priorityBadge}
          ${sentimentBadge}
        </div>
      </div>

      <div class="card-message">${m.text}</div>

      ${AISummaryCard(m.summary)}

      <div class="card-bottom">
        <span class="meta-item"><i class="fas fa-tag"></i> ${CATEGORY_LABELS[m.category] || m.category || '—'}</span>
        <span class="meta-item"><i class="fas fa-smile"></i> ${EMOTION_LABELS[m.emotion] || m.emotion || '—'}</span>
        ${complaintBadge ? `<span class="meta-item">${complaintBadge}</span>` : ''}
      </div>
    </div>
  `;
}

async function loadMessages() {
  const q = document.getElementById('searchInput').value;
  const sentiment = document.getElementById('sentimentFilter').value;
  const priority = document.getElementById('priorityFilter').value;
  const container = document.getElementById('messagesContainer');

  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (sentiment && sentiment !== 'all') params.set('sentiment', sentiment);
  if (priority && priority !== 'all') params.set('priority', priority);

  try {
    const messages = await apiGet(`/api/messages?${params.toString()}`);
    if (messages.length === 0) {
      container.innerHTML = '<div class="messages-empty"><i class="fas fa-envelope-open-text"></i><p>Сообщения не найдены</p></div>';
      return;
    }
    container.innerHTML = messages.map(m => MessageCard(m)).join('');
  } catch (e) {
    const msg = e.detail || e.message || 'Ошибка загрузки';
    container.innerHTML = `<div class="messages-empty"><i class="fas fa-exclamation-triangle"></i><p>${msg}</p></div>`;
  }
}

function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
  const icon = document.querySelector('.theme-toggle i');
  if (icon) icon.className = isDark ? 'fas fa-moon' : 'fas fa-sun';
}

document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  const icon = document.querySelector('.theme-toggle i');
  if (icon) icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  loadMessages();
});

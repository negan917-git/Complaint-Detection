let messagesLoaded = false;

async function loadMessages() {
  const q = document.getElementById('searchInput').value;
  const sentiment = document.getElementById('sentimentFilter').value;
  const priority = document.getElementById('priorityFilter').value;
  const tbody = document.getElementById('messagesBody');

  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (sentiment && sentiment !== 'all') params.set('sentiment', sentiment);
  if (priority && priority !== 'all') params.set('priority', priority);

  try {
    const messages = await apiGet(`/api/messages?${params.toString()}`);
    if (messages.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Сообщения не найдены</td></tr>';
      return;
    }
    tbody.innerHTML = messages.map(m => `
      <tr>
        <td><strong>${m.name || '—'}</strong> <span style="color:var(--text-secondary);font-size:12px;">@${m.username || ''}</span></td>
        <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${m.text}">${m.text}</td>
        <td>${sentimentTag(m.sentiment)}</td>
        <td>${m.emotion}</td>
        <td>${priorityTag(m.priority)}</td>
        <td>${m.category}</td>
        <td>${m.complaint ? '<span class="tag tag-complaint">Жалоба</span>' : '—'}</td>
        <td style="font-size:12px;color:var(--text-secondary);">${formatDate(m.created_at)}</td>
      </tr>
    `).join('');
    messagesLoaded = true;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Ошибка загрузки</td></tr>';
  }
}

document.addEventListener('DOMContentLoaded', loadMessages);

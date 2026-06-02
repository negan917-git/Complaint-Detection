async function analyzeAndSave() {
  const name = document.getElementById('simName').value.trim() || 'Аноним';
  const text = document.getElementById('simText').value.trim();
  if (!text) {
    showNotification('Введите текст сообщения', 'error');
    return;
  }

  const container = document.getElementById('analysisResultContainer');
  container.innerHTML = '<div style="text-align:center;padding:40px;"><span class="spinner spinner-dark" style="width:32px;height:32px;border-width:3px;"></span><p style="margin-top:16px;color:var(--text-secondary);">Анализ...</p></div>';

  try {
    const analysis = await apiPost('/api/analyze', { text });
    await apiPost('/api/messages', {
      name,
      text,
      summary: analysis.summary,
      sentiment: analysis.sentiment,
      emotion: analysis.emotion,
      priority: analysis.priority,
      category: analysis.category,
      complaint: analysis.complaint,
    });

    const analyzerLabel = analysis.analyzer === 'openai'
      ? '<span class="tag tag-positive" style="font-size:11px;">OpenAI</span>'
      : '<span class="tag tag-neutral" style="font-size:11px;">Локальный</span>';
    container.innerHTML = `
      <div class="analysis-result">
        <h3><i class="fas fa-check-circle" style="color:var(--success);"></i> Результат анализа ${analyzerLabel}</h3>
        <div class="result-grid">
          <div class="result-item">
            <div class="label">Тональность</div>
            <div class="value">${sentimentTag(analysis.sentiment)}</div>
          </div>
          <div class="result-item">
            <div class="label">Эмоция</div>
            <div class="value">${analysis.emotion}</div>
          </div>
          <div class="result-item">
            <div class="label">Категория</div>
            <div class="value">${analysis.category}</div>
          </div>
          <div class="result-item">
            <div class="label">Приоритет</div>
            <div class="value">${priorityTag(analysis.priority)}</div>
          </div>
          <div class="result-item">
            <div class="label">Жалоба</div>
            <div class="value">${analysis.complaint ? '<span class="tag tag-complaint">Да</span>' : '<span class="tag tag-positive">Нет</span>'}</div>
          </div>
          <div class="result-item" style="grid-column:1/-1;">
            <div class="label">Резюме</div>
            <div class="value">${analysis.summary}</div>
          </div>
        </div>
      </div>
    `;
    showNotification('Сохранено в базу данных', 'success');
    document.getElementById('simText').value = '';
  } catch (e) {
    const errorMsg = e.detail || e.message || e;
    container.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>Ошибка анализа</p><p style="font-size:12px;color:var(--danger);">${errorMsg}</p></div>`;
    showNotification('Ошибка анализа: ' + errorMsg, 'error');
  }
}

async function generateDemo() {
  const btn = document.getElementById('generateBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Генерация...';

  try {
    const res = await apiGet('/api/generate-demo');
    showNotification(`Сгенерировано ${res.generated} сообщений`, 'success');
  } catch (e) {
    showNotification(e.detail || e.message || 'Ошибка генерации', 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '<i class="fas fa-bolt"></i> Сгенерировать 10 демо сообщений';
}

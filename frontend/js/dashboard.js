let sentimentChartInstance = null;
let emotionChartInstance = null;

async function loadDashboard() {
  try {
    const data = await apiGet('/api/dashboard');
    document.getElementById('totalMessages').textContent = data.total_messages;
    document.getElementById('negativePercent').textContent = data.negative_percent + '%';
    document.getElementById('complaints').textContent = data.complaints;
    document.getElementById('activeBots').textContent = data.active_bots;
  } catch (e) {
    document.querySelectorAll('.stat-value').forEach(el => el.textContent = 'Ошибка');
  }

  try {
    const messages = await apiGet('/api/messages');
    const recentBody = document.getElementById('recentMessagesBody');
    if (messages.length === 0) {
      recentBody.innerHTML = '<tr><td colspan="4" class="empty-state">Нет сообщений</td></tr>';
    } else {
      recentBody.innerHTML = messages.slice(0, 10).map(m => `
        <tr>
          <td><strong>${m.name || '—'}</strong></td>
          <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${m.text}</td>
          <td>${sentimentTag(m.sentiment)}</td>
          <td>${priorityTag(m.priority)}</td>
        </tr>
      `).join('');
    }

    const total = messages.length;
    const pos = messages.filter(m => m.sentiment === 'positive').length;
    const neg = messages.filter(m => m.sentiment === 'negative').length;
    const neut = messages.filter(m => m.sentiment === 'neutral').length;

    const emotions = ['happy', 'neutral', 'confused', 'frustrated', 'angry'];
    const emotionCounts = emotions.map(e => messages.filter(m => m.emotion === e).length);

    if (sentimentChartInstance) sentimentChartInstance.destroy();
    if (emotionChartInstance) emotionChartInstance.destroy();

    const ctx1 = document.getElementById('sentimentChart').getContext('2d');
    sentimentChartInstance = new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: ['Positive', 'Negative', 'Neutral'],
        datasets: [{
          data: [pos, neg, neut],
          backgroundColor: ['#22c55e', '#ef4444', '#94a3b8'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true } }
        },
        cutout: '65%',
      }
    });

    const ctx2 = document.getElementById('emotionChart').getContext('2d');
    emotionChartInstance = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['Happy', 'Neutral', 'Confused', 'Frustrated', 'Angry'],
        datasets: [{
          data: emotionCounts,
          backgroundColor: ['#22c55e', '#94a3b8', '#f59e0b', '#ef4444', '#dc2626'],
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
          x: { grid: { display: false } }
        }
      }
    });
  } catch (e) {
    console.error('Dashboard error:', e);
  }
}

document.addEventListener('DOMContentLoaded', loadDashboard);

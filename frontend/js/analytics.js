let analyticsChartInstance = null;

async function loadAnalytics() {
  try {
    const data = await apiGet('/api/analytics');

    document.getElementById('totalAnalyzed').textContent = data.total_analyzed;
    document.getElementById('negativeShare').textContent = data.negative_share + '%';
    document.getElementById('complaintShare').textContent = data.complaint_share + '%';
    document.getElementById('topEmotion').textContent = data.top_emotion;

    if (analyticsChartInstance) analyticsChartInstance.destroy();

    const ctx = document.getElementById('analyticsChart').getContext('2d');
    const dates = data.daily_data.map(d => {
      const parts = d.date.split('-');
      return parts[2] + '.' + parts[1];
    });

    analyticsChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          {
            label: 'Все сообщения',
            data: data.daily_data.map(d => d.total),
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59,130,246,0.05)',
            fill: true,
            tension: 0.3,
            pointRadius: 3,
          },
          {
            label: 'Негативные',
            data: data.daily_data.map(d => d.negative),
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239,68,68,0.05)',
            fill: true,
            tension: 0.3,
            pointRadius: 3,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { position: 'top', labels: { usePointStyle: true } }
        },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
          x: { grid: { display: false } }
        },
        interaction: {
          intersect: false,
          mode: 'index',
        }
      }
    });

    const complaintsList = document.getElementById('topComplaintsList');
    if (data.top_complaints.length === 0) {
      complaintsList.innerHTML = '<div class="empty-state"><p>Нет жалоб</p></div>';
    } else {
      complaintsList.innerHTML = data.top_complaints.map((c, i) => `
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--border);">
          <span style="font-weight:600;color:var(--text-secondary);width:24px;">${i + 1}</span>
          <span style="flex:1;">${c.text}</span>
          <span class="tag tag-complaint">${c.count}</span>
        </div>
      `).join('');
    }

    const categoriesList = document.getElementById('categoriesList');
    if (data.categories.length === 0) {
      categoriesList.innerHTML = '<div class="empty-state"><p>Нет данных</p></div>';
    } else {
      const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];
      categoriesList.innerHTML = data.categories.map((c, i) => `
        <div class="category-item">
          <div class="cat-header">
            <span>${c.name}</span>
            <span>${c.count} (${c.percent}%)</span>
          </div>
          <div class="progress-bar">
            <div class="fill" style="width:${c.percent}%;background:${colors[i % colors.length]};"></div>
          </div>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error('Analytics error:', e);
  }
}

document.addEventListener('DOMContentLoaded', loadAnalytics);

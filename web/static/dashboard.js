// UNFOMO Dashboard
// Fetches data from /api/* endpoints served by server.py

const API = '';  // same origin

// ── Tab navigation ────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(s => s.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
  });
});

// ── Helpers ───────────────────────────────────────────────────────────────
function playerClass(player) {
  return `player-${player || 'other'}`;
}

function sigClass(sig) {
  return `sig-${Math.max(1, Math.min(5, sig || 1))}`;
}

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function emptyState(msg) {
  return `<div class="empty-state"><div class="icon">⚡</div>${msg}</div>`;
}

// ── Today tab ─────────────────────────────────────────────────────────────
async function loadToday() {
  document.getElementById('today-date').textContent =
    new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  try {
    const res = await fetch(`${API}/api/today`);
    const articles = await res.json();

    const list = document.getElementById('today-list');
    if (!articles.length) {
      list.innerHTML = emptyState('No articles yet — run the ingestion job to populate.');
      return;
    }

    list.innerHTML = articles.map(a => `
      <div class="article-card" onclick="window.open('${a.url}', '_blank')">
        <div class="card-top">
          <a class="card-title" href="${a.url}" target="_blank" rel="noopener"
             onclick="event.stopPropagation()">${a.title}</a>
          <div class="sig-badge ${sigClass(a.significance)}">${a.significance ?? '?'}</div>
        </div>
        ${a.summary_text ? `<p class="card-summary">${a.summary_text}</p>` : ''}
        ${a.now_what    ? `<div class="card-now-what">${a.now_what}</div>` : ''}
        <div class="card-meta">
          <span class="player-pill ${playerClass(a.ai_player)}">${a.ai_player || 'other'}</span>
          <span class="source-label">${a.source_name || ''}</span>
          <span class="source-label">${formatDate(a.published_at)}</span>
          ${(a.tags || []).slice(0, 3).map(t => `<span class="tag-pill">${t}</span>`).join('')}
        </div>
      </div>
    `).join('');
  } catch (e) {
    document.getElementById('today-list').innerHTML =
      emptyState('Could not load articles. Is the server running?');
  }
}

// ── Trends tab ────────────────────────────────────────────────────────────
async function loadTrends() {
  try {
    const res = await fetch(`${API}/api/trends`);
    const data = await res.json();

    if (!data.length) {
      document.getElementById('trend-chart').innerHTML = emptyState('No trend data yet.');
      return;
    }

    // Group by topic
    const byTopic = {};
    data.forEach(row => {
      if (!byTopic[row.name]) byTopic[row.name] = { x: [], y: [] };
      byTopic[row.name].x.push(row.date);
      byTopic[row.name].y.push(row.count);
    });

    const traces = Object.entries(byTopic).map(([name, vals]) => ({
      type: 'scatter',
      mode: 'lines+markers',
      name,
      x: vals.x,
      y: vals.y,
      line: { width: 2 },
      marker: { size: 5 },
    }));

    Plotly.newPlot('trend-chart', traces, {
      paper_bgcolor: 'transparent',
      plot_bgcolor:  'transparent',
      font:  { color: '#e8e8f0', family: 'Inter, sans-serif', size: 12 },
      xaxis: { gridcolor: '#2a2a3a', showgrid: true, color: '#7a7a9a' },
      yaxis: { gridcolor: '#2a2a3a', showgrid: true, color: '#7a7a9a', title: 'mentions' },
      legend: { bgcolor: 'transparent', font: { size: 11 } },
      margin: { t: 20, r: 20, b: 40, l: 40 },
      hovermode: 'x unified',
    }, { responsive: true, displayModeBar: false });

  } catch (e) {
    document.getElementById('trend-chart').innerHTML = emptyState('Could not load trend data.');
  }
}

// ── Players tab ───────────────────────────────────────────────────────────
async function loadPlayers() {
  try {
    const res = await fetch(`${API}/api/velocity`);
    const data = await res.json();

    if (!data.length) {
      document.getElementById('velocity-chart').innerHTML = emptyState('No velocity data yet.');
      return;
    }

    const COLORS = {
      anthropic: '#c084fc',
      openai:    '#60a5fa',
      google:    '#34d399',
      other:     '#94a3b8',
    };

    const players      = data.map(d => d.ai_player);
    const thisWeek     = data.map(d => d.this_week);
    const lastWeek     = data.map(d => d.last_week);
    const colors       = players.map(p => COLORS[p] || COLORS.other);

    const traces = [
      {
        type: 'bar', name: 'This week',
        x: players, y: thisWeek,
        marker: { color: colors, opacity: 1 },
      },
      {
        type: 'bar', name: 'Last week',
        x: players, y: lastWeek,
        marker: { color: colors, opacity: 0.4 },
      },
    ];

    Plotly.newPlot('velocity-chart', traces, {
      barmode: 'group',
      paper_bgcolor: 'transparent',
      plot_bgcolor:  'transparent',
      font:  { color: '#e8e8f0', family: 'Inter, sans-serif', size: 12 },
      xaxis: { gridcolor: '#2a2a3a', color: '#7a7a9a' },
      yaxis: { gridcolor: '#2a2a3a', color: '#7a7a9a', title: 'significant items' },
      legend: { bgcolor: 'transparent' },
      margin: { t: 20, r: 20, b: 40, l: 40 },
    }, { responsive: true, displayModeBar: false });

  } catch (e) {
    document.getElementById('velocity-chart').innerHTML = emptyState('Could not load velocity data.');
  }
}

// ── Emerging tab ──────────────────────────────────────────────────────────
async function loadEmerging() {
  try {
    const res = await fetch(`${API}/api/emerging`);
    const terms = await res.json();

    const list = document.getElementById('emerging-list');
    if (!terms.length) {
      list.innerHTML = emptyState('No emerging signals detected yet. Check back after a few days of data.');
      return;
    }

    list.innerHTML = terms.map(t => `
      <div class="emerging-card">
        <div>
          <div class="emerging-term">${t.term}</div>
          <div class="emerging-meta">First seen ${formatDate(t.first_seen_at)} · ${t.count_48h} mentions in 48h</div>
        </div>
        <span class="emerging-pill">EMERGING</span>
      </div>
    `).join('');
  } catch (e) {
    document.getElementById('emerging-list').innerHTML = emptyState('Could not load emerging signals.');
  }
}

// ── Weekly tab ────────────────────────────────────────────────────────────
async function loadWeekly() {
  try {
    const res = await fetch(`${API}/api/weekly`);
    const digest = await res.json();

    const content = document.getElementById('weekly-content');
    const podcast = document.getElementById('podcast-player');

    if (!digest || !digest.content) {
      content.innerHTML = emptyState('No weekly digest yet. It generates every Sunday.');
      return;
    }

    content.textContent = digest.content;

    if (digest.podcast_audio_url) {
      podcast.innerHTML = `
        <audio controls>
          <source src="${digest.podcast_audio_url}" type="audio/mpeg">
        </audio>`;
    }
  } catch (e) {
    document.getElementById('weekly-content').innerHTML = emptyState('Could not load weekly digest.');
  }
}

// ── Cost badge ────────────────────────────────────────────────────────────
async function loadCost() {
  try {
    const res = await fetch(`${API}/api/cost`);
    const data = await res.json();
    const total = data.reduce((sum, r) => sum + (r.total_cost_usd || 0), 0);
    document.getElementById('cost-badge').textContent = `$${total.toFixed(3)} / 30d`;
  } catch {
    document.getElementById('cost-badge').textContent = '';
  }
}

// ── Init ──────────────────────────────────────────────────────────────────
loadToday();
loadCost();

// Lazy-load other tabs on first click
const loaded = { today: true };
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    if (loaded[tab]) return;
    loaded[tab] = true;
    if (tab === 'trends')   loadTrends();
    if (tab === 'players')  loadPlayers();
    if (tab === 'emerging') loadEmerging();
    if (tab === 'weekly')   loadWeekly();
  });
});

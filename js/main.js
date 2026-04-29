/* ============================================================
   AttendX — Main JavaScript
   ============================================================ */

// ── THEME ──────────────────────────────────────────────────
const html = document.documentElement;
const themeKey = 'attendx_theme';

function applyTheme(theme) {
  html.setAttribute('data-theme', theme);
  const icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  }
  localStorage.setItem(themeKey, theme);
}

// Init theme
const savedTheme = localStorage.getItem(themeKey) || 'light';
applyTheme(savedTheme);

document.addEventListener('DOMContentLoaded', () => {

  // Apply theme icon on load
  const icon = document.getElementById('themeIcon');
  const currentTheme = html.getAttribute('data-theme');
  if (icon) icon.className = currentTheme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';

  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    });
  }

  // ── SIDEBAR TOGGLE ─────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('pageOverlay');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      const isMobile = window.innerWidth <= 768;
      if (isMobile) {
        sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('show');
      } else {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebar_collapsed', document.body.classList.contains('sidebar-collapsed'));
      }
    });
  }

  // Restore collapse state
  if (window.innerWidth > 768 && localStorage.getItem('sidebar_collapsed') === 'true') {
    document.body.classList.add('sidebar-collapsed');
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar?.classList.remove('open');
      overlay.classList.remove('show');
    });
  }

  // ── CURRENT DATE ──────────────────────────────────────
  const dateEl = document.getElementById('currentDate');
  if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  }

  // ── AUTO-DISMISS ALERTS ────────────────────────────────
  document.querySelectorAll('.custom-alert').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });

  // ── ATTENDANCE BUTTONS ─────────────────────────────────
  document.querySelectorAll('.att-row').forEach(row => {
    const presentBtn = row.querySelector('.present-btn');
    const absentBtn  = row.querySelector('.absent-btn');
    const hiddenInput = row.querySelector('input[type="checkbox"]');

    function updateRow(status) {
      if (status === 'present') {
        presentBtn?.classList.add('selected');
        absentBtn?.classList.remove('selected');
        if (hiddenInput) hiddenInput.checked = true;
        row.querySelector('.status-display')?.classList.add('is-present');
        row.querySelector('.status-display')?.classList.remove('is-absent');
      } else {
        absentBtn?.classList.add('selected');
        presentBtn?.classList.remove('selected');
        if (hiddenInput) hiddenInput.checked = false;
        row.querySelector('.status-display')?.classList.add('is-absent');
        row.querySelector('.status-display')?.classList.remove('is-present');
      }
    }

    presentBtn?.addEventListener('click', () => updateRow('present'));
    absentBtn?.addEventListener('click', () => updateRow('absent'));
  });

  // ── MARK ALL BUTTONS ───────────────────────────────────
  const markAllPresent = document.getElementById('markAllPresent');
  const markAllAbsent  = document.getElementById('markAllAbsent');

  markAllPresent?.addEventListener('click', () => {
    document.querySelectorAll('.present-btn').forEach(btn => btn.click());
  });
  markAllAbsent?.addEventListener('click', () => {
    document.querySelectorAll('.absent-btn').forEach(btn => btn.click());
  });

  // ── STUDENT SEARCH ─────────────────────────────────────
  const liveSearch = document.getElementById('liveSearch');
  if (liveSearch) {
    liveSearch.addEventListener('input', () => {
      const q = liveSearch.value.toLowerCase();
      document.querySelectorAll('.student-row').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
      });
    });
  }

  // ── CONFIRM DELETE ─────────────────────────────────────
  document.querySelectorAll('.confirm-delete').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm('Are you sure you want to delete this student? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  });

  // ── ANIMATE STAT NUMBERS ───────────────────────────────
  document.querySelectorAll('.stat-value[data-count]').forEach(el => {
    const target = parseInt(el.getAttribute('data-count'), 10);
    let current = 0;
    const step = Math.ceil(target / 40);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current + (el.dataset.suffix || '');
      if (current >= target) clearInterval(timer);
    }, 25);
  });

  // ── PROGRESS BARS ANIMATION ────────────────────────────
  setTimeout(() => {
    document.querySelectorAll('.pct-fill[data-width]').forEach(el => {
      el.style.width = el.getAttribute('data-width') + '%';
    });
  }, 200);

});


// ── CHART UTILITIES ────────────────────────────────────────
function getChartColors() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {
    grid: dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
    text: dark ? '#94A3B8' : '#64748B',
  };
}

function createTrendChart(canvasId, labels, presentData, absentData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const colors = getChartColors();

  return new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Present',
          data: presentData,
          borderColor: '#10B981',
          backgroundColor: 'rgba(16,185,129,0.08)',
          borderWidth: 2.5,
          pointBackgroundColor: '#10B981',
          pointRadius: 3,
          pointHoverRadius: 6,
          tension: 0.4,
          fill: true,
        },
        {
          label: 'Absent',
          data: absentData,
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239,68,68,0.06)',
          borderWidth: 2.5,
          pointBackgroundColor: '#EF4444',
          pointRadius: 3,
          pointHoverRadius: 6,
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: colors.text,
            usePointStyle: true,
            pointStyleWidth: 8,
            font: { family: 'Plus Jakarta Sans', weight: '600', size: 12 },
          },
        },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,0.9)',
          titleColor: '#E2E8F0',
          bodyColor: '#94A3B8',
          padding: 12,
          cornerRadius: 10,
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          grid: { color: colors.grid, drawBorder: false },
          ticks: { color: colors.text, font: { size: 11 } },
        },
        y: {
          grid: { color: colors.grid, drawBorder: false },
          ticks: { color: colors.text, font: { size: 11 } },
          beginAtZero: true,
        },
      },
    },
  });
}

function createDeptDonut(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const colors = getChartColors();

  return new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: ['#4F46E5','#10B981','#F59E0B','#3B82F6','#8B5CF6','#EC4899'],
        borderWidth: 2,
        borderColor: document.documentElement.getAttribute('data-theme') === 'dark' ? '#141827' : '#ffffff',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: colors.text,
            usePointStyle: true,
            pointStyleWidth: 8,
            padding: 12,
            font: { family: 'Plus Jakarta Sans', weight: '600', size: 12 },
          },
        },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,0.9)',
          titleColor: '#E2E8F0',
          bodyColor: '#94A3B8',
          padding: 12,
          cornerRadius: 10,
        },
      },
    },
  });
}

function createBarChart(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const colors = getChartColors();

  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Attendance %',
        data,
        backgroundColor: data.map(v =>
          v >= 75 ? 'rgba(16,185,129,0.8)' :
          v >= 50 ? 'rgba(245,158,11,0.8)' :
                    'rgba(239,68,68,0.8)'
        ),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,0.9)',
          titleColor: '#E2E8F0',
          bodyColor: '#94A3B8',
          padding: 12,
          cornerRadius: 10,
          callbacks: {
            label: ctx => ` ${ctx.parsed.y.toFixed(1)}%`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: colors.text, font: { size: 11 } },
        },
        y: {
          max: 100,
          grid: { color: colors.grid, drawBorder: false },
          ticks: { color: colors.text, font: { size: 11 }, callback: v => v + '%' },
          beginAtZero: true,
        },
      },
    },
  });
}

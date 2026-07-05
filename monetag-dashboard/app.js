/**
 * Monetag Revenue Dashboard — Shadow Del Valle R
 * Panel de control para revenue en vivo con Monetag SSP API v5
 */

// ─── State ───
const state = {
    currentSection: 'overview',
    revenueChart: null,
    autoRefresh: true,
    refreshInterval: null,
    data: {
        revenue: null,
        daily: null,
        zones: null,
        geo: null,
        alerts: null,
        optimize: null
    }
};

// ─── API Base ───
const API = {
    base: '/api/monetag',
    
    async get(endpoint, params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = `${this.base}${endpoint}${query ? '?' + query : ''}`;
        try {
            const res = await fetch(url);
            return await res.json();
        } catch (e) {
            console.error(`API Error: ${url}`, e);
            return { success: false, error: e.message };
        }
    },
    
    async post(endpoint, data = {}) {
        try {
            const res = await fetch(`${this.base}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await res.json();
        } catch (e) {
            console.error(`API Error POST: ${endpoint}`, e);
            return { success: false, error: e.message };
        }
    },
    
    // Shortcuts
    revenue: (force) => API.get('/revenue', { force: force ? '1' : '0' }),
    daily: (days) => API.get('/daily', { days: days || 30 }),
    zones: () => API.get('/zones'),
    geo: () => API.get('/geo'),
    alerts: (count) => API.get('/alerts', { count: count || 20 }),
    history: () => API.get('/history'),
    status: () => API.get('/status'),
    optimize: () => API.post('/optimize'),
    formatAnalysis: () => API.get('/optimize/format'),
    config: () => API.get('/config')
};

// ─── Navigation ───
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const section = item.dataset.section;
        navigateTo(section);
    });
});

function navigateTo(section) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`.nav-item[data-section="${section}"]`)?.classList.add('active');
    
    // Update section
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(`section-${section}`)?.classList.add('active');
    
    state.currentSection = section;
    
    // Load section data
    switch (section) {
        case 'overview': loadOverview(); break;
        case 'details': loadDetails(); break;
        case 'zones': loadZones(); break;
        case 'geo': loadGeo(); break;
        case 'alerts': loadAlerts(); break;
        case 'optimize': loadOptimize(); break;
    }
}

// ─── Initialization ───
document.addEventListener('DOMContentLoaded', () => {
    loadOverview();
    loadStatus();
    
    // Auto-refresh every 30 seconds
    state.refreshInterval = setInterval(() => {
        if (state.autoRefresh && state.currentSection === 'overview') {
            loadOverview(false);
            loadStatus();
        }
    }, 30000);
});

// ─── Status ───
async function loadStatus() {
    const status = await API.status();
    const dot = document.getElementById('apiStatusDot');
    const text = document.getElementById('apiStatusText');
    const sync = document.getElementById('lastSync');
    
    if (status.configured) {
        dot.className = 'status-dot online';
        text.textContent = 'Conectado';
    } else {
        dot.className = 'status-dot offline';
        text.textContent = 'Desconectado';
    }
    sync.textContent = status.last_sync || '—';
    
    // Alert badge
    const alertBadge = document.getElementById('alertBadge');
    const unacked = status.alert_stats?.unacknowledged || 0;
    alertBadge.textContent = unacked;
    alertBadge.style.display = unacked > 0 ? 'inline' : 'none';
}

// ─── Overview ───
async function loadOverview(showLoading = true) {
    const [revenue, daily, zones, geo] = await Promise.all([
        API.revenue(false),
        API.daily(30),
        API.zones(),
        API.geo()
    ]);
    
    state.data.revenue = revenue;
    state.data.daily = daily;
    state.data.zones = zones;
    state.data.geo = geo;
    
    if (revenue.success) {
        document.getElementById('kpiRevenue').textContent = `$${revenue.total_revenue?.toFixed(2) || '0.00'}`;
        document.getElementById('kpiRpm').textContent = `$${revenue.avg_rpm?.toFixed(2) || '0.00'}`;
        document.getElementById('kpiDaily').textContent = `$${revenue.avg_daily_revenue?.toFixed(2) || '0.00'}`;
        document.getElementById('kpiMonthly').textContent = `$${revenue.projected_monthly?.toFixed(2) || '0.00'}`;
        
        // Trends
        const trendEl = document.getElementById('kpiRevenueTrend');
        if (revenue.best_day?.date) {
            trendEl.textContent = `Mejor día: ${revenue.best_day.date} ($${revenue.best_day.revenue?.toFixed(2) || '0'})`;
        }
    }
    
    // Revenue Chart
    renderRevenueChart(daily);
    
    // Top Zones
    renderTopZones(zones);
    
    // Top Countries
    renderTopCountries(geo);
}

function renderRevenueChart(daily) {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;
    
    const entries = daily?.daily || [];
    const trend = daily?.trend_7d || [];
    
    if (state.revenueChart) {
        state.revenueChart.destroy();
    }
    
    if (entries.length === 0) {
        return;
    }
    
    const labels = entries.map(d => {
        const parts = d.date.split('-');
        return `${parts[1]}/${parts[2]}`;
    });
    const revenues = entries.map(d => d.revenue);
    const rpms = entries.map(d => parseFloat((d.rpm || 0).toFixed(2)));
    
    // Trend line
    const trendMap = {};
    trend.forEach(t => { trendMap[t.date] = t.moving_avg_7d; });
    const trendLine = entries.map(d => trendMap[d.date] || null);
    
    state.revenueChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Revenue',
                    data: revenues,
                    backgroundColor: 'rgba(108, 92, 231, 0.6)',
                    borderColor: '#6c5ce7',
                    borderWidth: 1,
                    borderRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: 'RPM',
                    data: rpms,
                    type: 'line',
                    borderColor: '#00cec9',
                    backgroundColor: 'rgba(0, 206, 201, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#00cec9',
                    tension: 0.3,
                    yAxisID: 'y1'
                },
                {
                    label: 'Tendencia (7d)',
                    data: trendLine,
                    type: 'line',
                    borderColor: '#fdcb6e',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0.4,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: { color: '#8888aa', font: { size: 11 } }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#8888aa', font: { size: 10 }, maxTicksLimit: 15 },
                    grid: { color: 'rgba(42,42,78,0.5)' }
                },
                y: {
                    position: 'left',
                    ticks: { color: '#8888aa', font: { size: 10 }, callback: v => '$' + v.toFixed(0) },
                    grid: { color: 'rgba(42,42,78,0.5)' }
                },
                y1: {
                    position: 'right',
                    ticks: { color: '#00cec9', font: { size: 10 }, callback: v => '$' + v.toFixed(1) },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderTopZones(zones) {
    const list = document.getElementById('topZonesList');
    const zoneList = zones?.zones || [];
    
    if (zoneList.length === 0) {
        list.innerHTML = '<div class="loading">Sin datos de zonas</div>';
        return;
    }
    
    const top = zoneList.slice(0, 5);
    list.innerHTML = top.map(z => `
        <div class="format-bar">
            <span class="format-label" style="min-width:0;flex:1">${z.zone_name || 'Zona'}</span>
            <span style="color:var(--accent2);font-weight:600;min-width:70px;text-align:right">$${z.revenue?.toFixed(2) || '0.00'}</span>
            <span style="color:var(--text2);font-size:0.75rem;min-width:40px;text-align:right">${z.revenue_percent?.toFixed(1) || 0}%</span>
        </div>
    `).join('');
}

function renderTopCountries(geo) {
    const list = document.getElementById('topCountriesList');
    const countries = geo?.countries || [];
    
    if (countries.length === 0) {
        list.innerHTML = '<div class="loading">Sin datos geográficos</div>';
        return;
    }
    
    const top = countries.slice(0, 5);
    list.innerHTML = top.map(c => `
        <div class="format-bar">
            <span class="format-label" style="min-width:0;flex:1">${c.country || '?'}</span>
            <span style="color:var(--accent2);font-weight:600;min-width:60px;text-align:right">$${c.rpm?.toFixed(2) || '0.00'}</span>
            <span style="color:var(--text2);font-size:0.75rem;min-width:50px;text-align:right">${c.ctr?.toFixed(1) || 0}%</span>
        </div>
    `).join('');
}

// ─── Details ───
async function loadDetails() {
    const days = parseInt(document.getElementById('detailDays')?.value || 30);
    const daily = await API.daily(days);
    const tbody = document.getElementById('detailBody');
    
    if (!daily.success || !daily.daily?.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Sin datos disponibles</td></tr>';
        return;
    }
    
    const entries = daily.daily.slice().reverse(); // más reciente primero
    tbody.innerHTML = entries.map(d => {
        const revenue = d.revenue || 0;
        const trend = revenue > 0 
            ? (revenue > 0.5 ? '📈' : '📉') 
            : '—';
        return `<tr>
            <td>${d.date || '—'}</td>
            <td style="color:var(--accent2);font-weight:600">$${revenue.toFixed(2)}</td>
            <td>${(d.impressions || 0).toLocaleString()}</td>
            <td>${(d.clicks || 0).toLocaleString()}</td>
            <td>$${(d.rpm || 0).toFixed(2)}</td>
            <td>${trend}</td>
        </tr>`;
    }).join('');
}

// ─── Zones ───
async function loadZones() {
    const zones = await API.zones();
    const tbody = document.getElementById('zonesBody');
    const zoneList = zones?.zones || [];
    
    if (zoneList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Sin datos de zonas</td></tr>';
        return;
    }
    
    tbody.innerHTML = zoneList.map(z => {
        const status = z.rpm > 2 ? '🔥' : (z.rpm > 0.5 ? '✅' : '⚠️');
        return `<tr>
            <td>${z.zone_name || 'Zona'}</td>
            <td style="color:var(--accent2);font-weight:600">$${z.revenue?.toFixed(2) || '0.00'}</td>
            <td>${z.revenue_percent?.toFixed(1) || 0}%</td>
            <td>$${z.rpm?.toFixed(2) || '0.00'}</td>
            <td>${(z.impressions || 0).toLocaleString()}</td>
            <td>${status}</td>
        </tr>`;
    }).join('');
}

// ─── Geo ───
async function loadGeo() {
    const geo = await API.geo();
    const tbody = document.getElementById('geoBody');
    const countries = geo?.countries || [];
    
    if (countries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Sin datos geográficos</td></tr>';
        return;
    }
    
    tbody.innerHTML = countries.map(c => {
        const tier = c.rpm > 2 ? 'Tier 1' : (c.rpm > 0.5 ? 'Tier 2' : 'Tier 3');
        const tierClass = c.rpm > 2 ? 'tier1' : (c.rpm > 0.5 ? 'tier2' : 'tier3');
        return `<tr>
            <td>${c.country || '?'}</td>
            <td style="color:var(--accent2);font-weight:600">$${c.revenue?.toFixed(2) || '0.00'}</td>
            <td>$${c.rpm?.toFixed(2) || '0.00'}</td>
            <td>${c.ctr?.toFixed(2) || 0}%</td>
            <td>${(c.impressions || 0).toLocaleString()}</td>
            <td class="${tierClass}">${tier}</td>
        </tr>`;
    }).join('');
}

// ─── Alerts ───
async function loadAlerts() {
    const data = await API.alerts(50);
    const list = document.getElementById('alertsList');
    const alerts = data?.alerts || [];
    
    if (alerts.length === 0) {
        list.innerHTML = '<div class="loading">🎉 Sin alertas. Todo en orden.</div>';
        return;
    }
    
    list.innerHTML = alerts.map(a => {
        const iconMap = { critical: '🔴', warning: '🟡', info: '🔵' };
        const icon = iconMap[a.severity] || '⚪';
        const rec = a.recommendation ? `<div class="alert-recommendation">💡 ${a.recommendation}</div>` : '';
        return `<div class="alert-item ${a.severity}">
            <div class="alert-icon">${icon}</div>
            <div class="alert-content">
                <div class="alert-title">${a.title || 'Alerta'}</div>
                <div class="alert-msg">${a.message || ''}</div>
                <div class="alert-date">${a.date || ''}</div>
                ${rec}
            </div>
        </div>`;
    }).join('');
}

async function ackAlerts() {
    await API.post('/alerts/acknowledge');
    loadAlerts();
    loadStatus();
}

// ─── Optimize ───
async function loadOptimize() {
    // Load config
    const config = await API.config();
    const configDiv = document.getElementById('monetagConfig');
    
    configDiv.innerHTML = `
        <div class="config-group">
            <label>API Token</label>
            <input type="password" id="apiToken" value="${config.api_token || ''}" placeholder="Ingresa tu token de Monetag">
        </div>
        <button class="btn btn-primary" onclick="saveConfig()">💾 Guardar Configuración</button>
    `;
}

async function saveConfig() {
    const token = document.getElementById('apiToken').value;
    const result = await API.post('/config', { api_token: token });
    if (result.success) {
        showToast('✅ Configuración guardada');
        loadStatus();
    } else {
        showToast('❌ Error: ' + (result.error || 'Desconocido'));
    }
}

async function runOptimization() {
    const btn = document.querySelector('.btn-primary');
    btn.textContent = '⏳ Optimizando...';
    btn.disabled = true;
    
    try {
        const result = await API.post('/optimize');
        displayOptimizationResults(result);
        showToast('✅ Optimización completada');
    } catch (e) {
        showToast('❌ Error: ' + e.message);
    } finally {
        btn.textContent = '🚀 Ejecutar Optimización';
        btn.disabled = false;
    }
}

function displayOptimizationResults(result) {
    // Format Analysis
    const formatDiv = document.getElementById('formatAnalysis');
    const formats = result?.format_analysis?.formats || [];
    
    if (formats.length === 0) {
        formatDiv.innerHTML = '<div class="loading">Sin datos de formatos</div>';
    } else {
        const maxRpm = Math.max(...formats.map(f => f.current_rpm), 1);
        formatDiv.innerHTML = formats.map(f => {
            const pct = (f.current_rpm / maxRpm * 100) || 0;
            const color = f.gap_to_avg > 0 ? 'var(--green)' : (f.gap_to_avg > -1 ? 'var(--yellow)' : 'var(--red)');
            return `<div class="format-bar">
                <span class="format-label">${f.format}</span>
                <div class="format-bar-track">
                    <div class="format-bar-fill" style="width:${pct}%;background:${color}">
                        $${f.current_rpm.toFixed(2)}
                    </div>
                </div>
                <span class="format-rpm" style="color:${color}">${f.status} $${f.current_rpm.toFixed(2)}</span>
            </div>`;
        }).join('');
    }
    
    // Recommendations
    const recDiv = document.getElementById('recommendationsList');
    const recommendations = result?.recommendations || [];
    
    if (recommendations.length === 0) {
        recDiv.innerHTML = '<div class="loading">No se generaron recomendaciones</div>';
    } else {
        recDiv.innerHTML = recommendations.map(r => 
            `<div class="recommendation-item">${r}</div>`
        ).join('');
    }
}

// ─── Refresh ───
async function refreshData() {
    const btn = document.querySelector('.header-actions .btn');
    btn.textContent = '⏳';
    await loadOverview(true);
    await loadStatus();
    btn.textContent = '🔄 Actualizar';
}

// ─── Toast ───
function showToast(msg) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px;
        background: var(--bg3); color: var(--text);
        padding: 12px 24px; border-radius: 8px;
        border: 1px solid var(--border);
        z-index: 1000; font-size: 0.9rem;
        animation: fadeIn 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(() => toast.remove(), 300); }, 3000);
}

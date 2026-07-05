/**
 * SEO Oracle Dashboard — Shadow Del Valle R
 * Panel de inteligencia de nichos con ranking FRR, proyecciones y plan de contenido
 */

// ─── State ───
const state = {
    currentSection: 'overview',
    niches: [],
    rankings: { frr: [], profit: [] }
};

// ─── API ───
const API = {
    async get(endpoint, params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = `${endpoint}${query ? '?' + query : ''}`;
        try {
            const res = await fetch(url);
            return await res.json();
        } catch (e) {
            console.error(`API Error: ${url}`, e);
            return { success: false, error: e.message };
        }
    },

    rankingFRR: () => API.get('/api/seo-oracle/ranking-frr'),
    rankingProfit: () => API.get('/api/seo-oracle/ranking-profit'),
    projection: (nicheId) => API.get('/api/seo-oracle/projection', { niche_id: nicheId }),
    plan: (nicheIds) => API.get('/api/seo-oracle/plan', { niches: nicheIds.join(',') }),
    stats: () => API.get('/api/seo-oracle/stats'),
    niches: () => API.get('/api/seo-oracle/niches'),
    exportReport: () => API.get('/api/seo-oracle/export')
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
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`.nav-item[data-section="${section}"]`)?.classList.add('active');
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(`section-${section}`)?.classList.add('active');
    state.currentSection = section;

    switch (section) {
        case 'overview': loadAllData(); break;
        case 'ranking-frr': loadFrrRanking(); break;
        case 'ranking-profit': loadProfitRanking(); break;
        case 'projection': loadProjectionSelect(); break;
        case 'plan': loadPlanSelect(); break;
        case 'stats': loadStats(); break;
    }
}

// ─── Initialization ───
document.addEventListener('DOMContentLoaded', () => {
    loadAllData();
});

// ─── Helpers ───
function fmt(n) {
    if (n === undefined || n === null) return '—';
    if (typeof n === 'number' && n >= 1000) return n.toLocaleString();
    if (typeof n === 'number') return n.toFixed(2);
    return n;
}

function fmtDollar(n) {
    if (n === undefined || n === null) return '$0';
    return '$' + (typeof n === 'number' ? n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : parseFloat(n).toFixed(2));
}

function confidenceBadge(level) {
    const map = { muy_alta: '🟢', alta: '🔵', media: '🟡', baja: '🔴' };
    return map[level] || '⚪';
}

function diffLabel(diff) {
    const map = { muy_baja: '🟢', baja: '🟢', media: '🟡', alta: '🟠', muy_alta: '🔴' };
    return map[diff] || '⚪';
}

// ─── Load Overview ───
async function loadAllData() {
    const [statsRes, frrRes, profitRes] = await Promise.all([
        API.stats(),
        API.rankingFRR(),
        API.rankingProfit()
    ]);

    state.rankings.frr = frrRes.ranking || [];
    state.rankings.profit = profitRes.ranking || [];

    if (statsRes.success) {
        document.getElementById('kpiTotal').textContent = statsRes.total_nichos || 0;
        document.getElementById('kpiAptos').textContent = statsRes.nichos_aptos || 0;
        document.getElementById('kpiFrrAvg').textContent = statsRes.frr_promedio_aptos?.toFixed(0) || '—';
        document.getElementById('kpiNodes').textContent = statsRes.total_nodos_trackeados || 0;
    }

    // Top 5 FRR
    const top5Frr = (frrRes.ranking || []).slice(0, 5);
    document.getElementById('top5Frr').innerHTML = top5Frr.length
        ? top5Frr.map(r => `
            <div class="format-bar">
                <span class="format-label" style="flex:1">${r.name}</span>
                <span style="color:var(--accent2);font-weight:600">FRR ${fmt(r.frr)}</span>
                <span style="color:var(--text2);font-size:0.75rem">${fmtDollar(r.cpc_avg)} CPC</span>
            </div>
        `).join('')
        : '<div class="loading">Sin datos</div>';

    // Top 5 Profit
    const top5Profit = (profitRes.ranking || []).slice(0, 5);
    document.getElementById('top5Profit').innerHTML = top5Profit.length
        ? top5Profit.map(r => `
            <div class="format-bar">
                <span class="format-label" style="flex:1">${r.name}</span>
                <span style="color:var(--accent2);font-weight:600">${fmt(r.profitability_score)}</span>
                <span style="color:var(--text2);font-size:0.75rem">${fmtDollar(r.cpc_avg)} CPC</span>
            </div>
        `).join('')
        : '<div class="loading">Sin datos</div>';

    // Categories
    if (statsRes.categorias) {
        document.getElementById('categoriesList').innerHTML = Object.entries(statsRes.categorias).map(([cat, data]) => `
            <div class="format-bar">
                <span class="format-label" style="flex:1;font-weight:600">${cat}</span>
                <span style="color:var(--text2)">${data.count} nichos</span>
                <span style="color:var(--accent2);font-weight:600;min-width:70px;text-align:right">CPC prom ${fmtDollar(data.cpc_promedio)}</span>
                <span style="color:var(--yellow);font-size:0.75rem;min-width:60px;text-align:right">FRR ${fmt(data.frr_promedio)}</span>
            </div>
        `).join('');
    }
}

// ─── FRR Ranking ───
async function loadFrrRanking() {
    const res = await API.rankingFRR();
    const tbody = document.getElementById('frrBody');

    if (!res.success || !res.ranking?.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="loading">Sin datos disponibles</td></tr>';
        return;
    }

    tbody.innerHTML = res.ranking.map((r, i) => {
        const status = r.apto ? '<span style="color:var(--green)">✅ APTO</span>' : '<span style="color:var(--red)">❌</span>';
        return `<tr>
            <td>${i + 1}</td>
            <td style="font-weight:600">${r.name}</td>
            <td style="color:var(--text2)">${r.category}</td>
            <td style="color:var(--accent2);font-weight:600">${fmtDollar(r.cpc_avg)}</td>
            <td>${fmt(r.search_volume)}</td>
            <td>${fmt(r.competencia)}</td>
            <td style="color:${r.apto ? 'var(--green)' : 'var(--red)'};font-weight:700">${fmt(r.frr)}</td>
            <td>${fmt(r.profitability_score)}</td>
            <td>${diffLabel(r.difficulty)} ${r.difficulty}</td>
            <td>${status}</td>
        </tr>`;
    }).join('');
}

// ─── Profitability Ranking ───
async function loadProfitRanking() {
    const res = await API.rankingProfit();
    const tbody = document.getElementById('profitBody');

    if (!res.success || !res.ranking?.length) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Sin datos disponibles</td></tr>';
        return;
    }

    tbody.innerHTML = res.ranking.map((r, i) => `<tr>
        <td>${i + 1}</td>
        <td style="font-weight:600">${r.name}</td>
        <td style="color:var(--text2)">${r.category}</td>
        <td style="color:var(--accent2);font-weight:600">${fmtDollar(r.cpc_avg)}</td>
        <td style="color:var(--green);font-weight:700">${fmt(r.profitability_score)}</td>
        <td>${fmt(r.frr)}</td>
        <td>${r.evergreen} / 10</td>
        <td>${diffLabel(r.difficulty)} ${r.difficulty}</td>
        <td>${r.language}</td>
    </tr>`).join('');
}

// ─── Projection ───
async function loadProjectionSelect() {
    const select = document.getElementById('projNicheSelect');
    if (select.options.length <= 1) {
        const res = await API.niches();
        if (res.success && res.niches) {
            res.niches.forEach(n => {
                const opt = document.createElement('option');
                opt.value = n.id;
                opt.textContent = `${n.name} (${fmtDollar(n.cpc_avg)})`;
                select.appendChild(opt);
            });
        }
    }
}

async function loadProjection() {
    const nicheId = document.getElementById('projNicheSelect').value;
    if (!nicheId) return;

    const res = await API.projection(nicheId);
    if (!res.success || !res.projection) {
        document.getElementById('projVisitors').textContent = 'Error';
        return;
    }

    const p = res.projection;
    document.getElementById('projVisitors').textContent = fmt(p.monthly_visitors_total);
    document.getElementById('projClicks').textContent = fmt(p.clicks_monthly);
    document.getElementById('projConfidence').textContent = `${confidenceBadge(p.confidence)} ${p.confidence.replace('_', ' ').toUpperCase()}`;

    document.getElementById('projMonthlyLow').textContent = fmtDollar(p.monthly_revenue.low);
    document.getElementById('projMonthlyAvg').textContent = fmtDollar(p.monthly_revenue.avg);
    document.getElementById('projMonthlyHigh').textContent = fmtDollar(p.monthly_revenue.high);
    document.getElementById('projYearlyLow').textContent = fmtDollar(p.yearly_revenue.low);
    document.getElementById('projYearlyAvg').textContent = fmtDollar(p.yearly_revenue.avg);
    document.getElementById('projYearlyHigh').textContent = fmtDollar(p.yearly_revenue.high);
}

// ─── Content Plan ───
async function loadPlanSelect() {
    const select = document.getElementById('planSelect');
    if (select.options.length === 0) {
        const res = await API.niches();
        if (res.success && res.niches) {
            res.niches.forEach(n => {
                const opt = document.createElement('option');
                opt.value = n.id;
                opt.textContent = `${n.name} (${fmtDollar(n.cpc_avg)})`;
                select.appendChild(opt);
            });
        }
    }
}

async function selectTop5() {
    if (!state.rankings.frr.length) {
        const res = await API.rankingFRR();
        state.rankings.frr = res.ranking || [];
    }
    const select = document.getElementById('planSelect');
    const top = state.rankings.frr.slice(0, 5).map(r => r.id);
    Array.from(select.options).forEach(opt => {
        opt.selected = top.includes(opt.value);
    });
    loadPlan();
}

function selectAll() {
    const select = document.getElementById('planSelect');
    Array.from(select.options).forEach(opt => opt.selected = true);
    loadPlan();
}

async function loadPlan() {
    const select = document.getElementById('planSelect');
    const selected = Array.from(select.options).filter(o => o.selected).map(o => o.value);

    if (selected.length === 0) {
        document.getElementById('planCount').textContent = '0';
        return;
    }

    const res = await API.plan(selected);
    if (!res.success || !res.plan) return;

    const p = res.plan;
    document.getElementById('planCount').textContent = p.nodes?.length || 0;
    document.getElementById('planVisitors').textContent = fmt(p.total_monthly_visitors);
    document.getElementById('planClicks').textContent = fmt(p.total_clicks);
    document.getElementById('planConfidence').textContent = p.confidence_promedio?.replace('_', ' ') || '—';

    document.getElementById('planMonthlyLow').textContent = fmtDollar(p.total_monthly_revenue.low);
    document.getElementById('planMonthlyAvg').textContent = fmtDollar(p.total_monthly_revenue.avg);
    document.getElementById('planMonthlyHigh').textContent = fmtDollar(p.total_monthly_revenue.high);
    document.getElementById('planYearlyLow').textContent = fmtDollar(p.total_yearly_revenue.low);
    document.getElementById('planYearlyAvg').textContent = fmtDollar(p.total_yearly_revenue.avg);
    document.getElementById('planYearlyHigh').textContent = fmtDollar(p.total_yearly_revenue.high);
}

// ─── Stats ───
async function loadStats() {
    const res = await API.stats();

    if (res.success) {
        document.getElementById('statsUmbral').textContent = res.umbral_frr || '—';
        document.getElementById('statsAptos').textContent = `${res.nichos_aptos || 0} / ${res.nichos_no_aptos || 0}`;
        document.getElementById('statsRevenue').textContent = fmtDollar(res.revenue_real_acumulado);
        document.getElementById('statsEvergreen').textContent = `${res.evergreen_5yr || '—'}x`;

        // Categories
        if (res.categorias) {
            document.getElementById('statsCategories').innerHTML = Object.entries(res.categorias).map(([cat, data]) => `
                <div class="format-bar">
                    <span style="flex:1;font-weight:600">${cat}</span>
                    <span style="color:var(--text2)">${data.count} nichos</span>
                    <span style="color:var(--accent2);min-width:70px;text-align:right">${fmtDollar(data.cpc_promedio)}</span>
                    <span style="color:var(--yellow);font-size:0.75rem;min-width:50px;text-align:right">FRR ${fmt(data.frr_promedio)}</span>
                </div>
            `).join('');
        }
    }

    // Evergreen table (local calculation)
    const years = [1, 2, 3, 5, 10];
    document.getElementById('statsEvergreenTable').innerHTML = years.map(y => {
        const mult = (0.9 ** y * (y - 1) + 1).toFixed(2);
        return `<div class="format-bar">
            <span style="flex:1">Año ${y}</span>
            <span style="color:var(--accent2);font-weight:600">${mult}x</span>
        </div>`;
    }).join('');
}

// ─── Export ───
async function exportReport() {
    const res = await API.exportReport();
    if (res.success) {
        showToast(`✅ Reporte exportado: ${res.filepath}`);
    } else {
        showToast('❌ Error exportando reporte');
    }
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
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

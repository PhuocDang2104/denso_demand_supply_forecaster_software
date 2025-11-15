/* ============================================
   DENSO FORECAST SUITE V3 - MAIN JAVASCRIPT
   ============================================ */

// ========== GLOBAL VARIABLES ==========
const main = document.getElementById("main");
const sidebar = document.getElementById("sidebar");
const roleSel = document.getElementById("role");
const notifBell = document.getElementById("notif-bell");
const notifPanel = document.getElementById("notif-panel");
const darkToggle = document.getElementById("btn-dark-toggle");

let ROLE = window.__ROLE__ || "viewer";
const ROLES = window.__ROLES__ || ["viewer"];

// ========== RBAC CONFIGURATION ==========
const RBAC = {
    viewer: { A: true, B: true, C: false, D: false },
    planner: { A: true, B: true, C: true, D: true },
    marketing: { A: true, B: true, C: true, D: false },
    manager: { A: true, B: true, C: true, D: true },
    admin: { A: true, B: true, C: true, D: true }
};

// ========== DENSO DATA ==========
const DENSO_SKUS = [
    { code: "K20PR-U",     name: "Spark Plug K20PR-U Standard",    category: "Ignition", type: "Copper Core" },
    { code: "SC20HR11",    name: "Spark Plug Iridium SC20HR11",    category: "Ignition", type: "Iridium" },
    { code: "IK20",        name: "Spark Plug Iridium Power IK20",  category: "Ignition", type: "Iridium Power" },
    { code: "IK22",        name: "Spark Plug Iridium TT IK22",     category: "Ignition", type: "Iridium TT" },
    { code: "K16R-U",      name: "Spark Plug K16R-U Compact",      category: "Ignition", type: "Copper Core" },
    { code: "INV-HEV-G1",  name: "Inverter HEV Gen1",              category: "Inverter", type: "HEV Inverter" },
    { code: "INV-PHEV-G2", name: "Inverter PHEV Gen2",             category: "Inverter", type: "PHEV Inverter" },
    { code: "INV-BEV-G1",  name: "Inverter BEV Platform A",        category: "Inverter", type: "BEV Inverter" }
];

const REGIONS = ["Vietnam", "Thailand", "Indonesia", "Philippines", "Malaysia", "Singapore"];
const CHANNELS = ["Dealer", "E-commerce", "OEM"];

// ========== INITIALIZATION ==========
(function init() {
    // Initialize role selector
    roleSel.innerHTML = ROLES.map(r => `<option value="${r}" ${r === ROLE ? 'selected' : ''}>${r.charAt(0).toUpperCase() + r.slice(1)}</option>`).join("");
    roleSel.addEventListener("change", (e) => {
        ROLE = e.target.value;
        navigate("A", "overview");
    });

    // Initialize sidebar toggle (mobile)
    document.getElementById("btn-toggle-sidebar")?.addEventListener("click", () => {
        sidebar.classList.toggle("open");
    });

    // Initialize notification bell
    notifBell.addEventListener("click", (e) => {
        e.stopPropagation();
        notifPanel.style.display = notifPanel.style.display === "block" ? "none" : "block";
    });

    // Close notification panel when clicking outside
    document.addEventListener("click", (e) => {
        if (!notifPanel.contains(e.target) && !notifBell.contains(e.target)) {
            notifPanel.style.display = "none";
        }
    });

    // Initialize dark mode toggle
    darkToggle?.addEventListener("click", toggleDarkMode);

    // Initialize nav group expand/collapse
    document.querySelectorAll(".nav-group-header").forEach(header => {
        header.addEventListener("click", () => {
            const group = header.dataset.group;
            const content = document.querySelector(`[data-group-content="${group}"]`);
            header.classList.toggle("collapsed");
            content.classList.toggle("collapsed");
        });
    });

    // Initialize nav links
    document.querySelectorAll(".nav-link").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const nav = link.dataset.nav;
            const subnav = link.dataset.subnav;
            navigate(nav, subnav);
        });
    });

    // Load initial page
    navigate("A", "overview");
})();

// ========== DARK MODE ==========
function toggleDarkMode() {
    const currentTheme = document.body.dataset.theme;
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.body.dataset.theme = newTheme;
    localStorage.setItem("theme", newTheme);
    darkToggle.querySelector("i").className = newTheme === "dark" ? "fas fa-sun" : "fas fa-moon";
}

// Load saved theme
const savedTheme = localStorage.getItem("theme") || "light";
document.body.dataset.theme = savedTheme;
if (darkToggle) {
    darkToggle.querySelector("i").className = savedTheme === "dark" ? "fas fa-sun" : "fas fa-moon";
}

// ========== NAVIGATION ==========
function navigate(nav, subnav = "") {
    // Check permissions
    if (!RBAC[ROLE][nav]) {
        lockPageIfNoPerm(nav);
        return;
    }

    // Update active nav link
    document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));
    const activeLink = document.querySelector(`[data-nav="${nav}"][data-subnav="${subnav}"]`);
    if (activeLink) activeLink.classList.add("active");

    // Expand nav group if collapsed
    const groupHeader = document.querySelector(`[data-group="${nav}"]`);
    const groupContent = document.querySelector(`[data-group-content="${nav}"]`);
    if (groupHeader?.classList.contains("collapsed")) {
        groupHeader.classList.remove("collapsed");
        groupContent?.classList.remove("collapsed");
    }

    // Close sidebar on mobile
    if (window.innerWidth < 992) {
        sidebar.classList.remove("open");
    }

    // Route to appropriate page
    const routeKey = `${nav}_${subnav}`;
    const routeMap = {
        "A_overview": renderDashboardOverview,
        "A_alerts": renderDashboardAlerts,
        "A_coverage": renderDashboardCoverage,
        "B_sku": renderForecastSKU,
        "B_backtest": renderForecastBacktest,
        "B_explain": renderForecastExplain,
        "C_scenario": renderScenarioLab,
        "C_campaign": renderCampaignImpact,
        "C_inventory": renderInventory,
        "D_exogenous": renderDataExogenous,
        "D_market": renderMarketIntelligence,  
        "D_monitoring": renderMonitoring,
        "D_registry": renderModelRegistry
    };

    const renderFunc = routeMap[routeKey];
    if (renderFunc) {
        renderFunc();
    } else {
        main.innerHTML = `<div class="alert alert-warning">Page not found: ${routeKey}</div>`;
    }
}

function lockPageIfNoPerm(navKey) {
    main.innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-lock fa-4x text-muted mb-3"></i>
            <h3>Access Denied</h3>
            <p class="text-muted">You don't have permission to view this section.</p>
            <p class="text-muted">Current role: <strong>${ROLE}</strong></p>
        </div>
    `;
}

// ========== API HELPER ==========
async function api(path, options = {}) {
    try {
        const res = await fetch(path, {
            ...options,
            headers: { "Content-Type": "application/json", ...options.headers }
        });
        return await res.json();
    } catch (err) {
        console.error("API Error:", err);
        return null;
    }
}

// ========== UTILITY FUNCTIONS ==========
function formatNumber(num, decimals = 2) {
    return parseFloat(num).toFixed(decimals);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString("vi-VN");
}

function showLoading() {
    main.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Loading...</p>
        </div>
    `;
}

// ========== A. DASHBOARD RENDERING ==========

// A.1 Dashboard Overview
async function renderDashboardOverview(filters = {}) {
    showLoading();

    // build query string từ filters
    const params = new URLSearchParams();
    if (filters.sku)     params.append("sku", filters.sku);
    if (filters.region)  params.append("country", filters.region);
    if (filters.channel) params.append("channel", filters.channel);
    if (filters.mode)    params.append("mode", filters.mode);

    const qs = params.toString();
    const data = await api(`/api/dashboard${qs ? "?" + qs : ""}`);
    if (!data) {
        main.innerHTML = '<div class="alert alert-danger">Failed to load dashboard data</div>';
        return;
    }

    main.innerHTML = `
        <div class="fade-in">
            <!-- Page Header -->
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="mb-1">Dashboard Overview</h2>
                    <p class="text-muted mb-0">Denso Southeast Asia - 4-8 Week Forecast</p>
                </div>
                <div>
                    <button class="btn btn-outline-primary btn-sm me-2"><i class="fas fa-sync-alt me-1"></i>Refresh</button>
                    <button class="btn btn-primary btn-sm"><i class="fas fa-download me-1"></i>Export</button>
                </div>
            </div>

            <!-- Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-3">
                            <label class="form-label small text-muted">SKU</label>
                            <select class="form-select form-select-sm" id="filter-sku">
                                <option value="">All SKUs</option>
                                ${DENSO_SKUS.map(s => `<option value="${s.code}">${s.code} - ${s.name}</option>`).join("")}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label small text-muted">Region</label>
                            <select class="form-select form-select-sm" id="filter-region">
                                <option value="">All Regions</option>
                                ${REGIONS.map(r => `<option value="${r}">${r}</option>`).join("")}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label small text-muted">Channel</label>
                            <select class="form-select form-select-sm" id="filter-channel">
                                <option value="">All Channels</option>
                                ${CHANNELS.map(c => `<option value="${c}">${c}</option>`).join("")}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label small text-muted">Forecast Mode</label>
                            <select class="form-select form-select-sm" id="filter-mode">
                                <option value="baseline">Baseline</option>
                                <option value="scenario">Scenario</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KPI Cards -->
            <div class="grid-4 mb-4">
                <div class="card kpi-card border-primary">
                    <div class="card-body">
                        <i class="fas fa-chart-line icon-bg text-primary"></i>
                        <div class="label">Revenue P50 (4 weeks)</div>
                        <div class="value text-primary">$${data.kpi.revenue_p50}M</div>
                        <div class="change text-success"><i class="fas fa-arrow-up me-1"></i>+12.3%</div>
                    </div>
                </div>
                <div class="card kpi-card border-info">
                    <div class="card-body">
                        <i class="fas fa-chart-area icon-bg text-info"></i>
                        <div class="label">Range P10-P90</div>
                        <div class="value text-info">$${data.kpi.range_p10_p90[0]}-${data.kpi.range_p10_p90[1]}M</div>
                        <div class="change text-muted"><i class="fas fa-minus me-1"></i>Stable</div>
                    </div>
                </div>
                <div class="card kpi-card border-warning">
                    <div class="card-body">
                        <i class="fas fa-percentage icon-bg text-warning"></i>
                        <div class="label">MAPE (Last Week)</div>
                        <div class="value text-warning">${data.kpi.mape_last_week}%</div>
                        <div class="change ${data.kpi.mape_last_week < 10 ? 'text-success' : 'text-danger'}">
                            <i class="fas fa-${data.kpi.mape_last_week < 10 ? 'check' : 'exclamation-triangle'} me-1"></i>
                            ${data.kpi.mape_last_week < 10 ? 'Good' : 'Review'}
                        </div>
                    </div>
                </div>
                <div class="card kpi-card border-success">
                    <div class="card-body">
                        <i class="fas fa-check-double icon-bg text-success"></i>
                        <div class="label">Coverage (28 days)</div>
                        <div class="value text-success">${data.kpi.coverage_28d}%</div>
                        <div class="change text-success"><i class="fas fa-arrow-up me-1"></i>+2.1%</div>
                    </div>
                </div>
            </div>

            <!-- Fan Chart & Alerts -->
            <div class="row g-4 mb-4">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-chart-area me-2"></i>Forecast Fan Chart (P10/P50/P90)
                        </div>
                        <div class="card-body">
                            <canvas id="fanChart" height="80"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card" style="max-height: 400px; overflow-y: auto;">
                        <div class="card-header">
                            <i class="fas fa-exclamation-triangle me-2"></i>Alerts (${data.alerts.length})
                        </div>
                        <div class="card-body p-2">
                            ${data.alerts.map(a => `
                                <div class="alert-item ${a.level}">
                                    <div class="d-flex align-items-start gap-2">
                                        <i class="fas fa-${a.level === 'high' ? 'exclamation-circle' : a.level === 'med' ? 'exclamation-triangle' : 'info-circle'} mt-1"></i>
                                        <div class="flex-grow-1">
                                            <div class="fw-bold text-uppercase small">${a.type.replace(/_/g, ' ')}</div>
                                            <div class="small">${a.msg}</div>
                                        </div>
                                    </div>
                                </div>
                            `).join("")}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Category Breakdown -->
            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-layer-group me-2"></i>Forecast by Category
                        </div>
                        <div class="card-body">
                            <canvas id="categoryChart" height="100"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header">
                            <i class="fas fa-exclamation-triangle me-2"></i>Risky SKUs (High Error)
                        </div>
                        <div class="card-body">
                            <div class="list-group list-group-flush">
                                ${data.kpi.risky_skus.map((sku, i) => {
                                    const skuObj = DENSO_SKUS.find(s => s.code === sku) || { code: sku, name: "Unknown" };
                                    return `
                                        <div class="list-group-item d-flex justify-content-between align-items-center">
                                            <div>
                                                <div class="fw-bold">${skuObj.code}</div>
                                                <div class="small text-muted">${skuObj.name}</div>
                                            </div>
                                            <span class="badge bg-danger">${(Math.random() * 20 + 15).toFixed(1)}% MAPE</span>
                                        </div>
                                    `;
                                }).join("")}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    const skuSel     = document.getElementById("filter-sku");
    const regionSel  = document.getElementById("filter-region");
    const channelSel = document.getElementById("filter-channel");
    const modeSel    = document.getElementById("filter-mode");

    // Set lại giá trị đang chọn (để giữ state khi reload)
    if (filters.sku && skuSel)       skuSel.value = filters.sku;
    if (filters.region && regionSel) regionSel.value = filters.region;
    if (filters.channel && channelSel) channelSel.value = filters.channel;
    if (filters.mode && modeSel)     modeSel.value = filters.mode;

    const applyFilters = () => {
        const newFilters = {
            sku:     skuSel.value     || undefined,
            region:  regionSel.value  || undefined,
            channel: channelSel.value || undefined,
            mode:    modeSel.value    || undefined
        };
        renderDashboardOverview(newFilters);
    };

    skuSel?.addEventListener("change", applyFilters);
    regionSel?.addEventListener("change", applyFilters);
    channelSel?.addEventListener("change", applyFilters);
    modeSel?.addEventListener("change", applyFilters);

    // Render charts
    renderFanChart(data.fan);
    renderCategoryChart(data.fan.by_category);
}

// A.2 Dashboard Alerts
async function renderDashboardAlerts() {
    showLoading();
    const data = await api("/api/dashboard");
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-exclamation-triangle text-warning me-2"></i>Alert Center</h2>

            <div class="row g-4">
                ${data.alerts.map(a => `
                    <div class="col-md-6">
                        <div class="card alert-item ${a.level}">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h5 class="card-title mb-0">
                                        <span class="badge bg-${a.level === 'high' ? 'danger' : a.level === 'med' ? 'warning' : 'info'} me-2">${a.level.toUpperCase()}</span>
                                        ${a.type.replace(/_/g, ' ').toUpperCase()}
                                    </h5>
                                    <small class="text-muted">2 mins ago</small>
                                </div>
                                <p class="card-text">${a.msg}</p>
                                <a href="${a.link}" class="btn btn-sm btn-outline-primary">Investigate <i class="fas fa-arrow-right ms-1"></i></a>
                            </div>
                        </div>
                    </div>
                `).join("")}
            </div>
        </div>
    `;
}

// A.3 Dashboard Coverage
async function renderDashboardCoverage() {
    showLoading();
    const data = await api("/api/dashboard");
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-check-double text-success me-2"></i>Coverage & Error Analysis</h2>

            <div class="row g-4">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header">Coverage Heatmap (P10-P90) by Channel & Week</div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-bordered table-sm text-center">
                                    <thead>
                                        <tr>
                                            <th>Channel</th>
                                            ${data.coverage.weeks.map(w => `<th>${w}</th>`).join("")}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.coverage.channels.map((ch, i) => `
                                            <tr>
                                                <td class="fw-bold">${ch}</td>
                                                ${data.coverage.grid[i].map(val => `
                                                    <td style="background: ${val > 90 ? '#d4edda' : val > 80 ? '#fff3cd' : '#f8d7da'}">
                                                        ${val}%
                                                    </td>
                                                `).join("")}
                                            </tr>
                                        `).join("")}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">Error by Horizon</div>
                        <div class="card-body">
                            <canvas id="errorHorizonChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render Error Horizon Chart
    const ctx = document.getElementById("errorHorizonChart");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.error_horizon.horizons.map(h => `${h} days`),
            datasets: [{
                label: "MAPE %",
                data: data.error_horizon.errors,
                backgroundColor: "rgba(220, 53, 69, 0.7)"
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } }
        }
    });
}

// ========== B. FORECAST RENDERING ==========

// B.1 Forecast by SKU
async function renderForecastSKU(skuCode) {
    showLoading();

    // Nếu không truyền skuCode (lần đầu từ navigate) thì default = SKU đầu tiên
    const sku = skuCode || DENSO_SKUS[0].code;

    const data = await api(`/api/forecast/sku?sku=${encodeURIComponent(sku)}`);
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-box text-primary me-2"></i>Forecast by SKU</h2>

            <!-- SKU Selector -->
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row g-3 align-items-end">
                        <div class="col-md-4">
                            <label class="form-label">Select SKU</label>
                            <select class="form-select" id="sku-select" onchange="onSkuSelectChange(this.value)">
                                ${DENSO_SKUS.map(s => `
                                    <option value="${s.code}" ${s.code === data.sku.code ? 'selected' : ''}>
                                        ${s.code} - ${s.name}
                                    </option>
                                `).join("")}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Channel</label>
                            <select class="form-select"><option>All</option>${CHANNELS.map(c => `<option>${c}</option>`).join("")}</select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Region</label>
                            <select class="form-select"><option>All</option>${REGIONS.map(r => `<option>${r}</option>`).join("")}</select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Horizon</label>
                            <select class="form-select"><option>28 days</option><option>56 days</option></select>
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-primary w-100"><i class="fas fa-sync-alt me-1"></i>Refresh</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SKU Info -->
            <div class="alert alert-info">
                <strong>${data.sku.code}</strong> - ${data.sku.name} | Category: <span class="badge bg-primary">${data.sku.category}</span>
            </div>

            <!-- Fan Chart -->
            <div class="card mb-4">
                <div class="card-header"><i class="fas fa-chart-area me-2"></i>Forecast Fan Chart</div>
                <div class="card-body">
                    <canvas id="skuFanChart" height="80"></canvas>
                </div>
            </div>

            <!-- Components & SHAP -->
            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header"><i class="fas fa-puzzle-piece me-2"></i>Prophet Components</div>
                        <div class="card-body">
                            <canvas id="componentsChart" height="100"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header"><i class="fas fa-lightbulb me-2"></i>Top Features (SHAP Global)</div>
                        <div class="card-body">
                            <canvas id="shapChart" height="100"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Regressors Table -->
            <div class="card mt-4">
                <div class="card-header"><i class="fas fa-table me-2"></i>Regressor Status</div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-modern">
                            <thead><tr><th>Feature</th><th>Status</th></tr></thead>
                            <tbody>
                                ${data.regressors.map(r => `
                                    <tr>
                                        <td>${r.name}</td>
                                        <td><span class="badge bg-${r.status === 'ok' ? 'success' : 'warning'}">${r.status}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render charts
    renderSKUFanChart(data.fan);
    renderComponentsChart(data.components);
    renderSHAPChart(data.shap_global);
}

// B.2 Backtest Leaderboard
async function renderForecastBacktest() {
    showLoading();
    const data = await api("/api/forecast/backtest");
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-trophy text-warning me-2"></i>Backtest Leaderboard</h2>

            <div class="card">
                <div class="card-header">Model Performance Comparison</div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-modern table-hover">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Model</th>
                                    <th>sMAPE ↓</th>
                                    <th>MAE ↓</th>
                                    <th>Pinball(P90) ↓</th>
                                    <th>Coverage ↑</th>
                                    <th>Latency (s)</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.leaderboard.sort((a, b) => a.sMAPE - b.sMAPE).map((m, i) => `
                                    <tr>
                                        <td><span class="badge bg-${i === 0 ? 'success' : i === 1 ? 'info' : 'secondary'}">#${i + 1}</span></td>
                                        <td><strong>${m.model}</strong></td>
                                        <td>${m.sMAPE}%</td>
                                        <td>${m.MAE}</td>
                                        <td>${m.PinballP90}</td>
                                        <td><span class="badge bg-${m.Coverage > 85 ? 'success' : 'warning'}">${m.Coverage}%</span></td>
                                        <td>${m.Latency}s</td>
                                        <td><button class="btn btn-sm btn-primary" onclick="setChampion('${m.model}')">Set Champion</button></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// B.3 Forecast Explain (SHAP)
async function renderForecastExplain() {
    showLoading();
    const sku = DENSO_SKUS[0].code;
    const data = await api(`/api/forecast/sku?sku=${sku}`);
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-lightbulb text-info me-2"></i>Model Explainability (SHAP)</h2>

            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header">Global Feature Importance</div>
                        <div class="card-body">
                            <canvas id="shapGlobalChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header">Local Explanation (${data.shap_local.date})</div>
                        <div class="card-body">
                            <canvas id="shapLocalChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render SHAP charts
    const ctxGlobal = document.getElementById("shapGlobalChart");
    new Chart(ctxGlobal, {
        type: "bar",
        data: {
            labels: data.shap_global.map(s => s.feature),
            datasets: [{
                label: "Importance",
                data: data.shap_global.map(s => s.importance),
                backgroundColor: "rgba(13, 110, 253, 0.7)"
            }]
        },
        options: { indexAxis: "y", responsive: true }
    });

    const ctxLocal = document.getElementById("shapLocalChart");
    new Chart(ctxLocal, {
        type: "bar",
        data: {
            labels: data.shap_local.items.map(s => s.feature),
            datasets: [{
                label: "Impact",
                data: data.shap_local.items.map(s => s.impact),
                backgroundColor: data.shap_local.items.map(s => s.impact > 0 ? "rgba(25, 135, 84, 0.7)" : "rgba(220, 53, 69, 0.7)")
            }]
        },
        options: { indexAxis: "y", responsive: true }
    });
}

// ========== C. SCENARIO & CAMPAIGN & INVENTORY ==========

// C.1 Scenario Lab
async function renderScenarioLab() {
    showLoading();

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-flask text-success me-2"></i>Scenario Lab</h2>

            <div class="card mb-4">
                <div class="card-header">What-If Analysis</div>
                <div class="card-body">
                    <div class="row g-4">
                        <div class="col-md-3">
                            <label class="form-label">Price Change (%)</label>
                            <input type="range" class="form-range" id="price-delta" min="-30" max="30" value="0" oninput="updateScenario()">
                            <div class="text-center"><span id="price-delta-val">0%</span></div>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Promo Depth</label>
                            <input type="range" class="form-range" id="promo-depth" min="0" max="0.5" step="0.05" value="0" oninput="updateScenario()">
                            <div class="text-center"><span id="promo-depth-val">0%</span></div>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Ad Spend</label>
                            <input type="range" class="form-range" id="ad-spend" min="0" max="2" step="0.1" value="0" oninput="updateScenario()">
                            <div class="text-center"><span id="ad-spend-val">0x</span></div>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Forecast Result</label>
                            <div class="card bg-primary text-white">
                                <div class="card-body p-2 text-center">
                                    <h3 class="mb-0" id="scenario-result">$135.0</h3>
                                    <small>Revenue Forecast</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">Scenario Comparison</div>
                <div class="card-body">
                    <canvas id="scenarioChart" height="80"></canvas>
                </div>
            </div>
        </div>
    `;
}

// C.2 Campaign Impact
async function renderCampaignImpact() {
    showLoading();
    const data = await api("/api/campaign/impact");
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-bullhorn text-warning me-2"></i>Campaign Impact Analysis</h2>

            <!-- Impact Cards -->
            <div class="grid-4 mb-4">
                <div class="card border-success">
                    <div class="card-body text-center">
                        <h6 class="text-muted">Absolute Lift</h6>
                        <h2 class="text-success">${data.cards.abs_lift}</h2>
                    </div>
                </div>
                <div class="card border-primary">
                    <div class="card-body text-center">
                        <h6 class="text-muted">Relative Lift</h6>
                        <h2 class="text-primary">${data.cards.rel_lift}%</h2>
                    </div>
                </div>
                <div class="card border-info">
                    <div class="card-body text-center">
                        <h6 class="text-muted">P-Value</h6>
                        <h2 class="text-info">${data.cards.p_value}</h2>
                    </div>
                </div>
                <div class="card border-warning">
                    <div class="card-body text-center">
                        <h6 class="text-muted">ROI</h6>
                        <h2 class="text-warning">${data.cards.roi}x</h2>
                    </div>
                </div>
            </div>

            <!-- Counterfactual Chart -->
            <div class="card mb-4">
                <div class="card-header">Observed vs Counterfactual</div>
                <div class="card-body">
                    <canvas id="campaignChart"></canvas>
                </div>
            </div>

            <!-- Reasons -->
            <div class="card">
                <div class="card-header">Key Success Factors</div>
                <div class="card-body">
                    <ul class="list-group list-group-flush">
                        ${data.reasons.map(r => `<li class="list-group-item"><i class="fas fa-check-circle text-success me-2"></i>${r}</li>`).join("")}
                    </ul>
                </div>
            </div>
        </div>
    `;

    // Render Campaign Chart
    const ctx = document.getElementById("campaignChart");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: data.days,
            datasets: [
                { label: "Observed", data: data.observed, borderColor: "rgb(13, 110, 253)", fill: false },
                { label: "Counterfactual", data: data.counterfactual, borderColor: "rgb(220, 53, 69)", borderDash: [5, 5], fill: false }
            ]
        },
        options: { responsive: true }
    });
}

// C.3 Inventory
async function renderInventory() {
    showLoading();

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-warehouse text-primary me-2"></i>Inventory Recommendations</h2>

            <div class="card mb-4">
                <div class="card-header">Input Parameters</div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-3">
                            <label class="form-label">Service Level</label>
                            <input type="number" class="form-control" id="service-level" value="0.95" step="0.01" min="0.8" max="0.99">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Lead Time (days)</label>
                            <input type="number" class="form-control" id="lead-time" value="7">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">On Hand</label>
                            <input type="number" class="form-control" id="on-hand" value="100">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">On Order</label>
                            <input type="number" class="form-control" id="on-order" value="40">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">MOQ</label>
                            <input type="number" class="form-control" id="moq" value="24">
                        </div>
                    </div>
                    <button class="btn btn-primary mt-3" onclick="calculateInventory()"><i class="fas fa-calculator me-1"></i>Calculate</button>
                </div>
            </div>

            <div id="inventory-result"></div>
        </div>
    `;
}

async function calculateInventory() {
    const body = {
        service_level: parseFloat(document.getElementById("service-level").value),
        lead_time: parseInt(document.getElementById("lead-time").value),
        on_hand: parseInt(document.getElementById("on-hand").value),
        on_order: parseInt(document.getElementById("on-order").value),
        moq: parseInt(document.getElementById("moq").value)
    };

    const data = await api("/api/inventory/recommend", { method: "POST", body: JSON.stringify(body) });
    if (!data) return;

    document.getElementById("inventory-result").innerHTML = `
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card border-primary">
                    <div class="card-body text-center">
                        <h6 class="text-muted">Base Stock (S)</h6>
                        <h2 class="text-primary">${data.base_stock}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-warning">
                    <div class="card-body text-center">
                        <h6 class="text-muted">Safety Stock</h6>
                        <h2 class="text-warning">${data.safety_stock}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-success">
                    <div class="card-body text-center">
                        <h6 class="text-muted">PO Recommend</h6>
                        <h2 class="text-success">${data.po_recommend}</h2>
                    </div>
                </div>
            </div>
        </div>
        <div class="alert alert-info mt-3">
            <strong>Reason:</strong> ${data.reason}
        </div>
    `;
}

// ========== D. DATA & MONITORING & MODEL ==========

// D.1 Data Exogenous - Updated with real data structure from paste-4.txt
async function renderDataExogenous() {
    showLoading();
    const data = await api("/api/data/exogenous");
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4">Exogenous Data - Denso Sparkplug Dataset</h2>
            
            <!-- Dataset Info -->
            <div class="alert alert-info mb-4">
                <strong>Dataset:</strong> 10_sparkplug_dataset_final.csv - Weekly forecast data (W-MON) from 2022-01-03 to 2025-10-20<br>
                <strong>Features:</strong> Economic indicators, market drivers, internal commercial factors, and external events
            </div>

            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span>Recent 30 Days - Prophet & XGBoost Features</span>
                    <div>
                        <button class="btn btn-sm btn-outline-primary"><i class="fas fa-upload me-1"></i>Import</button>
                        <button class="btn btn-sm btn-primary"><i class="fas fa-download me-1"></i>Export</button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-modern table-striped">
                            <thead>
                                <tr>
                                    <th>Date (ds)</th>
                                    <th>PMI</th>
                                    <th>GDP Growth (%)</th>
                                    <th>CPI (%)</th>
                                    <th>Gas Price (VND)</th>
                                    <th>GTrends Score</th>
                                    <th>New ICE+Hybrid Sales</th>
                                    <th>BEV Penetration (%)</th>
                                    <th>Weather Event</th>
                                    <th>Holiday Flag</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.rows.slice(0, 15).map(row => `
                                    <tr>
                                        <td>${formatDate(row.ds)}</td>
                                        <td><span class="badge bg-${row.pmi > 50 ? 'success' : 'warning'}">${row.pmi}</span></td>
                                        <td>${row.gdp_growth}%</td>
                                        <td>${row.cpi}%</td>
                                        <td>${new Intl.NumberFormat('vi-VN').format(row.gas_price)}</td>
                                        <td><div class="progress" style="width:60px;height:20px"><div class="progress-bar" style="width:${row.gtrends_score}%">${row.gtrends_score}</div></div></td>
                                        <td>${new Intl.NumberFormat('vi-VN').format(Math.round(row.new_ice_and_hybrid_sales))}</td>
                                        <td><span class="badge bg-${row.bev_penetration_rate > 0.3 ? 'danger' : row.bev_penetration_rate > 0.1 ? 'warning' : 'secondary'}">${(row.bev_penetration_rate * 100).toFixed(1)}%</span></td>
                                        <td><i class="fas fa-${row.weather_event_flag ? 'bolt text-danger' : 'sun text-success'}"></i></td>
                                        <td><i class="fas fa-${row.holiday_flag ? 'star text-warning' : 'minus text-muted'}"></i></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Feature Categories -->
                    <div class="row mt-4">
                        <div class="col-md-3">
                            <h6 class="text-primary">Economic Macro</h6>
                            <small class="text-muted">PMI, GDP Growth, CPI (from GSO, S&P Global)</small>
                        </div>
                        <div class="col-md-3">
                            <h6 class="text-success">Market Demand</h6>
                            <small class="text-muted">Gas Price, Vehicle Sales, Google Trends</small>
                        </div>
                        <div class="col-md-3">
                            <h6 class="text-info">Vehicle Fleet</h6>
                            <small class="text-muted">ICE+Hybrid fleet size, BEV penetration</small>
                        </div>
                        <div class="col-md-3">
                            <h6 class="text-warning">Events</h6>
                            <small class="text-muted">Weather events, holidays (Tet, national days)</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// D.3 Monitoring - Updated with real features from paste-4.txt
async function renderMonitoring() {
    showLoading();
    const data = await api("/api/monitoring");
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-heartbeat text-danger me-2"></i>Model & Data Monitoring</h2>

            <!-- Drift Table -->
            <div class="card mb-4">
                <div class="card-header">Data Drift Detection - Prophet & XGBoost Features</div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-modern">
                            <thead>
                                <tr>
                                    <th>Feature</th>
                                    <th>Type</th>
                                    <th>KS Statistic</th>
                                    <th>PSI</th>
                                    <th>Status</th>
                                    <th>Source</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Economic Macro Features -->
                                <tr>
                                    <td><strong>pmi</strong></td>
                                    <td><span class="badge bg-primary">Economic</span></td>
                                    <td>0.08</td>
                                    <td>0.05</td>
                                    <td><span class="badge bg-success">Stable</span></td>
                                    <td>GSO / S&P Global</td>
                                </tr>
                                <tr>
                                    <td><strong>gdp_growth</strong></td>
                                    <td><span class="badge bg-primary">Economic</span></td>
                                    <td>0.12</td>
                                    <td>0.09</td>
                                    <td><span class="badge bg-success">Stable</span></td>
                                    <td>GSO</td>
                                </tr>
                                <tr>
                                    <td><strong>cpi</strong></td>
                                    <td><span class="badge bg-primary">Economic</span></td>
                                    <td>0.15</td>
                                    <td>0.13</td>
                                    <td><span class="badge bg-warning">Medium</span></td>
                                    <td>GSO</td>
                                </tr>
                                <!-- Market Demand Features -->
                                <tr>
                                    <td><strong>gas_price</strong></td>
                                    <td><span class="badge bg-success">Demand</span></td>
                                    <td>0.18</td>
                                    <td>0.16</td>
                                    <td><span class="badge bg-warning">Medium</span></td>
                                    <td>Ministry of Industry</td>
                                </tr>
                                <tr>
                                    <td><strong>gtrends_score</strong></td>
                                    <td><span class="badge bg-success">Demand</span></td>
                                    <td>0.22</td>
                                    <td>0.19</td>
                                    <td><span class="badge bg-warning">Medium</span></td>
                                    <td>Google Trends</td>
                                </tr>
                                <tr>
                                    <td><strong>total_new_vehicle_sales</strong></td>
                                    <td><span class="badge bg-success">Demand</span></td>
                                    <td>0.25</td>
                                    <td>0.23</td>
                                    <td><span class="badge bg-danger">High Drift</span></td>
                                    <td>VAMA, Industry Reports</td>
                                </tr>
                                <!-- Fleet Dynamics -->
                                <tr>
                                    <td><strong>new_ice_and_hybrid_sales</strong></td>
                                    <td><span class="badge bg-info">Fleet</span></td>
                                    <td>0.28</td>
                                    <td>0.26</td>
                                    <td><span class="badge bg-danger">High Drift</span></td>
                                    <td>VAMA, TC Motor</td>
                                </tr>
                                <tr>
                                    <td><strong>bev_penetration_rate</strong></td>
                                    <td><span class="badge bg-info">Fleet</span></td>
                                    <td>0.35</td>
                                    <td>0.31</td>
                                    <td><span class="badge bg-danger">High Drift</span></td>
                                    <td>Industry Reports, VinFast</td>
                                </tr>
                                <tr>
                                    <td><strong>total_ice_and_hybrid_on_road</strong></td>
                                    <td><span class="badge bg-info">Fleet</span></td>
                                    <td>0.14</td>
                                    <td>0.11</td>
                                    <td><span class="badge bg-warning">Medium</span></td>
                                    <td>Vehicle Registry, GSO</td>
                                </tr>
                                <!-- Commercial Internal -->
                                <tr>
                                    <td><strong>own_price_aftermarket</strong></td>
                                    <td><span class="badge bg-warning">Commercial</span></td>
                                    <td>0.07</td>
                                    <td>0.04</td>
                                    <td><span class="badge bg-success">Stable</span></td>
                                    <td>ERP / Sales DB</td>
                                </tr>
                                <tr>
                                    <td><strong>comp_price_aftermarket</strong></td>
                                    <td><span class="badge bg-warning">Commercial</span></td>
                                    <td>0.19</td>
                                    <td>0.17</td>
                                    <td><span class="badge bg-warning">Medium</span></td>
                                    <td>Market Intelligence</td>
                                </tr>
                                <tr>
                                    <td><strong>promo_depth</strong></td>
                                    <td><span class="badge bg-warning">Commercial</span></td>
                                    <td>0.11</td>
                                    <td>0.08</td>
                                    <td><span class="badge bg-success">Stable</span></td>
                                    <td>Marketing DB</td>
                                </tr>
                                <!-- Events -->
                                <tr>
                                    <td><strong>weather_event_flag</strong></td>
                                    <td><span class="badge bg-secondary">Event</span></td>
                                    <td>0.06</td>
                                    <td>0.03</td>
                                    <td><span class="badge bg-success">Stable</span></td>
                                    <td>National Weather Center</td>
                                </tr>
                                <tr>
                                    <td><strong>holiday_flag</strong></td>
                                    <td><span class="badge bg-secondary">Event</span></td>
                                    <td>0.02</td>
                                    <td>0.01</td>
                                    <td><span class="badge bg-success">Stable</span></td>
                                    <td>Public Calendar</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Drift Summary -->
                    <div class="row mt-3">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-success">Stable Features</h6>
                                <span class="badge bg-success" style="font-size:1.2rem;">6</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-warning">Medium Drift</h6>
                                <span class="badge bg-warning" style="font-size:1.2rem;">6</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-danger">High Drift</h6>
                                <span class="badge bg-danger" style="font-size:1.2rem;">3</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-info">Total Features</h6>
                                <span class="badge bg-info" style="font-size:1.2rem;">15</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Model Performance -->
            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header">Rolling Model Performance</div>
                        <div class="card-body">
                            <canvas id="rollingChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header">Coverage by SKU</div>
                        <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr><th>SKU</th><th>Channel</th><th>Coverage</th></tr>
                                    </thead>
                                    <tbody>
                                        ${data.coverage.slice(0, 10).map(c => `
                                            <tr>
                                                <td><small>${c.sku}</small></td>
                                                <td><small>${c.channel}</small></td>
                                                <td><span class="badge bg-${c.coverage > 85 ? 'success' : 'warning'}">${c.coverage}%</span></td>
                                            </tr>
                                        `).join("")}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Render Rolling Performance Chart
    const ctx = document.getElementById("rollingChart");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: data.rolling.map(r => r.week),
            datasets: [
                { label: "sMAPE", data: data.rolling.map(r => r.sMAPE), borderColor: "rgb(220, 53, 69)", fill: false },
                { label: "MAE", data: data.rolling.map(r => r.MAE), borderColor: "rgb(13, 110, 253)", fill: false }
            ]
        },
        options: { responsive: true }
    });
}

// D.4 Model Registry
async function renderModelRegistry() {
    showLoading();
    const data = await api("/api/models/registry");
    if (!data) return;

    main.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4"><i class="fas fa-code-branch text-info me-2"></i>Model Registry</h2>

            <!-- Model Table -->
            <div class="card mb-4">
                <div class="card-header">Registered Models</div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-modern">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Version</th>
                                    <th>Trained At</th>
                                    <th>Dataset</th>
                                    <th>Parameters</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.models.map(m => `
                                    <tr>
                                        <td><strong>${m.name}</strong></td>
                                        <td><span class="badge bg-secondary">${m.version}</span></td>
                                        <td>${formatDate(m.trained_at)}</td>
                                        <td><code>${m.dataset}</code></td>
                                        <td><pre class="mb-0 small">${JSON.stringify(m.params, null, 2)}</pre></td>
                                        <td>
                                            <button class="btn btn-sm btn-primary" onclick="setChampion('${m.name}@${m.version}')">Set Champion</button>
                                        </td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Metrics Timeline -->
            <div class="card">
                <div class="card-header">Model Metrics Over Time</div>
                <div class="card-body">
                    <canvas id="metricsChart"></canvas>
                </div>
            </div>
        </div>
    `;

    // Render Metrics Chart
    const ctx = document.getElementById("metricsChart");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.metrics.map(m => m.name),
            datasets: [
                { label: "sMAPE", data: data.metrics.map(m => m.sMAPE), backgroundColor: "rgba(220, 53, 69, 0.7)" },
                { label: "MAE", data: data.metrics.map(m => m.MAE), backgroundColor: "rgba(13, 110, 253, 0.7)" }
            ]
        },
        options: { responsive: true }
    });
}

// ========== D.2 MARKET INTELLIGENCE (UPDATED WITH DENSO DATA INSIGHTS) ==========

let marketMap = null;
let currentMapMode = "price";
let selectedSKUs = [];

let mapLayers = {};
const REGION_COORDS_FRONT = {
    "Vietnam":     [21.0285, 105.8542],   // Hanoi
    "Thailand":    [13.7563, 100.5018],   // Bangkok
    "Indonesia":   [-6.2088, 106.8456],   // Jakarta
    "Philippines": [14.5995, 120.9842],   // Manila
    "Malaysia":    [3.1390, 101.6869],    // Kuala Lumpur
    "Singapore":   [1.3521, 103.8198]     // Singapore
};
async function initMarketMap() {
    // Use simple fallback map if Mapbox token not available
    const mapContainer = document.getElementById("map3d");

    // For demo purposes, create a simple SVG-based map
    mapContainer.innerHTML = `
        <div style="width:100%;height:100%;background:linear-gradient(135deg,#1e3c72 0%,#2a5298 100%);display:flex;align-items:center;justify-content:center;color:white;font-size:1.2rem;">
            <div class="text-center">
                <i class="fas fa-map-marked-alt fa-4x mb-3"></i>
                <div>Southeast Asia 3D Map</div>
                <div class="small mt-2 text-white-50">Interactive visualization of market data</div>
                <div id="map-pins" class="mt-4"></div>
            </div>
        </div>
    `;

    marketMap = { initialized: true };
}
async function renderMarketIntelligence() {
    showLoading();

    main.innerHTML = `
        <div class="fade-in">
            <!-- Header -->
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2 class="mb-1"><i class="fas fa-globe-asia text-primary me-2"></i>Market Intelligence</h2>
                    <p class="text-muted mb-0">Real-time market data, pricing, weather, logistics - Southeast Asia</p>
                </div>
                <div>
                    <button class="btn btn-outline-primary btn-sm me-2" onclick="refreshMarketData()">
                        <i class="fas fa-sync-alt me-1"></i>Refresh Data
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="exportMarketData()">
                        <i class="fas fa-download me-1"></i>Export Report
                    </button>
                </div>
            </div>

            <!-- AI NEWS AGENT DASHBOARD -->
            <div class="card mb-4 border-info">
                <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                    <div>
                        <i class="fas fa-robot me-2"></i>AI Market News Agent - Web Scraping Insights
                    </div>
                    <button class="btn btn-sm btn-light" onclick="refreshNewsAgent()">
                        <i class="fas fa-sync-alt me-1"></i>Cập nhật từ web
                    </button>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <!-- Sheet storage -->
                        <div class="col-lg-7">
                            <h6 class="mb-2">
                                <i class="fas fa-table me-1"></i>Sheet Storage (Scraped Articles)
                            </h6>
                            <div class="table-responsive" id="news-sheet-table">
                                <div class="text-muted small">Đang tải dữ liệu tin tức từ agent...</div>
                            </div>
                        </div>

                        <!-- AI conclusion (2 box: Report & Conclusion) -->
                        <div class="col-lg-5 d-flex flex-column gap-3">
                            <!-- Box 1: Báo cáo phân tích rủi ro -->
                            <div>
                                <h6 class="mb-2">
                                    <i class="fas fa-file-alt me-1"></i>Báo cáo phân tích rủi ro từ Agent
                                </h6>
                                <div id="news-ai-summary"
                                    class="border rounded p-3 small bg-light"
                                    style="max-height:180px; overflow-y:auto;">
                                    <div class="text-muted">
                                        Agent đang đọc dữ liệu trên sheet và tạo báo cáo tổng hợp...
                                    </div>
                                </div>
                            </div>

                            <!-- Box 2: Kết luận (Conclusion) -->
                            <div>
                                <h6 class="mb-2">
                                    <i class="fas fa-flag-checkered me-1"></i>Kết luận (Conclusion)
                                </h6>
                                <div id="news-ai-conclusion"
                                    class="border rounded p-3 small bg-light"
                                    style="max-height:80px; overflow-y:auto;">
                                    <div class="text-muted">
                                        Khi agent tạo kết luận, phần này sẽ hiển thị tóm tắt rủi ro chính.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- DENSO FORECAST INSIGHTS DASHBOARD -->
            <div class="card mb-4 border-primary">
                <div class="card-header bg-primary text-white">
                    <i class="fas fa-chart-line me-2"></i>DENSO Forecast Dataset Insights - Prophet & XGBoost Model Features
                </div>
                <div class="card-body">
                    <!-- Key Insights Cards -->
                    <div class="row g-3 mb-4">
                        <div class="col-md-3">
                            <div class="card border-success">
                                <div class="card-body text-center p-3">
                                    <i class="fas fa-car fa-2x text-success mb-2"></i>
                                    <h6 class="text-success">Vehicle Market Evolution</h6>
                                    <h4 class="mb-1">ICE → BEV</h4>
                                    <small class="text-muted">BEV penetration: 2% → 45% (2022-2025)</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card border-info">
                                <div class="card-body text-center p-3">
                                    <i class="fas fa-chart-bar fa-2x text-info mb-2"></i>
                                    <h6 class="text-info">Market Segmentation</h6>
                                    <h4 class="mb-1">OEM + AM</h4>
                                    <small class="text-muted">Separate channels: B2B vs B2C dynamics</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card border-warning">
                                <div class="card-body text-center p-3">
                                    <i class="fas fa-database fa-2x text-warning mb-2"></i>
                                    <h6 class="text-warning">Dataset Scope</h6>
                                    <h4 class="mb-1">194 weeks</h4>
                                    <small class="text-muted">2022-01-03 to 2025-10-20 (W-MON)</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card border-danger">
                                <div class="card-body text-center p-3">
                                    <i class="fas fa-cogs fa-2x text-danger mb-2"></i>
                                    <h6 class="text-danger">Features Count</h6>
                                    <h4 class="mb-1">22 features</h4>
                                    <small class="text-muted">Economic, Commercial, Events, Fleet</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Feature Analysis Chart -->
                    <div class="row">
                        <div class="col-md-6">
                            <canvas id="featureImportanceChart"></canvas>
                        </div>
                        <div class="col-md-6">
                            <canvas id="channelTrendsChart"></canvas>
                        </div>
                    </div>

                    <!-- Key Data Drivers -->
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <h6 class="text-primary"><i class="fas fa-arrow-up me-1"></i>Positive Drivers (Aftermarket)</h6>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>total_ice_and_hybrid_on_road</strong></span>
                                    <span class="badge bg-success">Baseline trend</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>gdp_growth, pmi</strong></span>
                                    <span class="badge bg-success">Economic boost</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>gtrends_score</strong></span>
                                    <span class="badge bg-success">Intent signal</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>comp_price_aftermarket</strong></span>
                                    <span class="badge bg-success">Competitive advantage</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>promo_depth</strong></span>
                                    <span class="badge bg-success">Promotional lift</span>
                                </li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-danger"><i class="fas fa-arrow-down me-1"></i>Negative Drivers</h6>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>bev_penetration_rate</strong></span>
                                    <span class="badge bg-danger">Long-term threat</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>cpi</strong></span>
                                    <span class="badge bg-danger">Inflation pressure</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>gas_price</strong></span>
                                    <span class="badge bg-danger">Reduced usage</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>own_price_aftermarket</strong></span>
                                    <span class="badge bg-danger">Price elasticity</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span><strong>weather_event_flag</strong></span>
                                    <span class="badge bg-danger">Temporary disruption</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SKU Selector -->
            <div class="card mb-4">
                <div class="card-header">
                    <i class="fas fa-box me-2"></i>Select SKUs for Market Analysis
                </div>
                <div class="card-body">
                    <div class="row g-2">
                        ${DENSO_SKUS.slice(0, 10).map(sku => `
                            <div class="col-md-2">
                                <div class="form-check">
                                    <input class="form-check-input sku-checkbox" type="checkbox" value="${sku.code}" id="sku-${sku.code}" onchange="updateMarketData()">
                                    <label class="form-check-label small" for="sku-${sku.code}" title="${sku.name}">
                                        ${sku.code}
                                    </label>
                                </div>
                            </div>
                        `).join("")}
                    </div>
                </div>
            </div>

            <!-- Market Stats Summary -->
            <div id="market-stats" class="mb-4"></div>

            <!-- 3D Map Container -->
            <div class="card mb-4">
                <div class="card-header">
                    <i class="fas fa-map me-2"></i>Southeast Asia Interactive Map
                    <span class="badge bg-info ms-2">2D</span>
                </div>
                <div class="card-body p-0">
                    <div class="map-container">
                        <!-- Mapbox 3D Map -->
                        <div id="map3d"></div>

                        <!-- Collapsible Map Controls -->
                        <div class="map-controls-wrapper collapsed" id="map-controls-wrapper"
                            onmouseenter="openMapControls()" onmouseleave="closeMapControls()">
                            <div class="map-controls-tab">
                                <i class="fas fa-layer-group"></i>
                            </div>
                            <div class="map-controls-panel">
                                <h6 class="mb-3"><i class="fas fa-layer-group me-2"></i>Map Layers</h6>
                                <button class="map-mode-btn active" onclick="changeMapMode('price')" id="btn-mode-price">
                                    <i class="fas fa-dollar-sign"></i>Price Heatmap
                                </button>
                                <button class="map-mode-btn" onclick="changeMapMode('weather')" id="btn-mode-weather">
                                    <i class="fas fa-cloud-sun"></i>Weather Conditions
                                </button>
                                <button class="map-mode-btn" onclick="changeMapMode('port')" id="btn-mode-port">
                                    <i class="fas fa-ship"></i>Port & Logistics
                                </button>
                                <button class="map-mode-btn" onclick="changeMapMode('warehouse')" id="btn-mode-warehouse">
                                    <i class="fas fa-warehouse"></i>Warehouses
                                </button>
                                <button class="map-mode-btn" onclick="changeMapMode('sku')" id="btn-mode-sku">
                                    <i class="fas fa-box"></i>SKU Distribution
                                </button>
                            </div>
                        </div>

                        <!-- Map Legend -->
                        <div class="map-legend" id="map-legend">
                            <h6 class="mb-2"><i class="fas fa-info-circle me-2"></i>Legend</h6>
                            <div id="legend-content"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Detailed Tables -->
            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header"><i class="fas fa-dollar-sign me-2"></i>Price by Region</div>
                        <div class="card-body" id="price-table"></div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-header"><i class="fas fa-cloud-sun me-2"></i>Weather Impact</div>
                        <div class="card-body" id="weather-table"></div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Load AI News Agent data
    await updateNewsAgentSection();

    // Initialize map and load data
    await initMarketMap();
    await updateMarketData();
    
    // Render DENSO insights charts
    renderFeatureImportanceChart();
    renderChannelTrendsChart();
}

// New functions for DENSO insights
function renderFeatureImportanceChart() {
    const ctx = document.getElementById("featureImportanceChart");
    if (!ctx) return;

    const featureData = {
        labels: [
            'total_ice_and_hybrid_on_road',
            'new_ice_and_hybrid_sales', 
            'bev_penetration_rate',
            'gdp_growth',
            'promo_depth',
            'own_price_aftermarket',
            'cpi',
            'gas_price'
        ],
        datasets: [{
            label: 'Feature Importance (Aftermarket)',
            data: [0.85, 0.72, -0.68, 0.45, 0.42, -0.38, -0.35, -0.28],
            backgroundColor: [
                '#198754', '#0d6efd', '#dc3545', '#198754', '#198754', '#dc3545', '#dc3545', '#dc3545'
            ]
        }]
    };

    new Chart(ctx, {
        type: 'bar',
        data: featureData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Key Feature Importance (Synthetic Data Model)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Importance Score'
                    }
                }
            }
        }
    });
}

function renderChannelTrendsChart() {
    const ctx = document.getElementById("channelTrendsChart");
    if (!ctx) return;

    const trendData = {
        labels: ['2022 Q1', '2022 Q2', '2022 Q3', '2022 Q4', '2023 Q1', '2023 Q2', '2023 Q3', '2023 Q4', '2024 Q1', '2024 Q2', '2024 Q3', '2024 Q4', '2025 Q1', '2025 Q2', '2025 Q3'],
        datasets: [
            {
                label: 'OEM Channel (B2B)',
                data: [3200, 3150, 3300, 3250, 3180, 3220, 3100, 3050, 2980, 2900, 2850, 2750, 2600, 2450, 2300],
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                fill: false
            },
            {
                label: 'Aftermarket Channel (B2C)',
                data: [4800, 4950, 5100, 5200, 5300, 5450, 5200, 5100, 5250, 5400, 5300, 5150, 5000, 4850, 4700],
                borderColor: '#198754',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                fill: false
            }
        ]
    };

    new Chart(ctx, {
        type: 'line',
        data: trendData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Channel Performance Trends (Weekly Average)'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Units Sold'
                    }
                }
            }
        }
    });
}

// ========== AI NEWS AGENT SECTION ==========

// Gọi API lấy dữ liệu sheet + summary
async function updateNewsAgentSection() {
    try {
        const res = await api("/api/market/news_agent");

        if (!res) return;

        renderNewsSheetTable(res.storage || []);
        renderNewsAgentSummary(res.summary || "", res.conclusion || "");
    } catch (e) {
        console.error("updateNewsAgentSection error:", e);
        renderNewsSheetTable([]);
        renderNewsAgentSummary("", "");
    }
}

async function refreshNewsAgent() {
    await updateNewsAgentSection();
    alert("✓ Agent đã cập nhật tin tức mới nhất!");
}

// storage: array các bài scrape được
// mỗi item mình giả định dạng:
// { title, category, region, published_at, source, url, headline, snippet }
function renderNewsSheetTable(storage) {
    const div = document.getElementById("news-sheet-table");
    if (!div) return;

    if (!storage || storage.length === 0) {
        div.innerHTML = `
            <div class="text-muted small">
                Chưa có dữ liệu nào trong sheet. Agent chưa scrape được bài viết phù hợp hôm nay.
            </div>
        `;
        return;
    }

    const rowsHtml = storage.slice(0, 10).map(item => `
        <tr>
            <td>
                <div class="fw-semibold small">${item.title || "(Không có tiêu đề)"}</div>
                ${item.headline ? `<div class="small text-muted">${item.headline}</div>` : ""}
            </td>
            <td class="small">${item.region || "-"}</td>
            <td class="small">${item.category || "-"}</td>
            <td class="small">
                ${item.published_at
                    ? new Date(item.published_at).toLocaleString("vi-VN")
                    : "-"
                }
            </td>
            <td class="small">
                ${item.source || "-"}<br/>
                ${item.url
                    ? `<a href="${item.url}" target="_blank" rel="noopener" class="small">Mở link</a>`
                    : ""
                }
            </td>
        </tr>
    `).join("");

    div.innerHTML = `
         <table class="table table-sm align-middle mb-0">
            <thead>
                <tr class="text-center">
                    <th style="width:40%">Tiêu đề / Headline</th>
                    <th style="width:10%">Region</th>
                    <th style="width:10%">Category</th>
                    <th style="width:20%">Thời gian</th>
                    <th style="width:20%">Nguồn</th>
                </tr>
            </thead>
            <tbody>
                ${rowsHtml}
            </tbody>
        </table>
        <div class="mt-2 text-muted small">
            Hiển thị tối đa 10 bản ghi mới nhất từ sheet (agent scrape).
        </div>
    `;
}

// summaryText: phần báo cáo chính (trước Conclusion)
// conclusionText: phần KẾT LUẬN (CONCLUSION)
function renderNewsAgentSummary(summaryText, conclusionText) {
    const divSummary = document.getElementById("news-ai-summary");
    const divConclusion = document.getElementById("news-ai-conclusion");

    if (!divSummary || !divConclusion) return;

    // Fallback: nếu chưa có gì cả
    if ((!summaryText || !summaryText.trim()) && (!conclusionText || !conclusionText.trim())) {
        divSummary.innerHTML = `
            <div class="text-muted small">
                Chưa có báo cáo nào từ agent. Khi agent chạy xong, phần tóm tắt sẽ hiển thị ở đây.
            </div>
        `;
        divConclusion.innerHTML = `
            <div class="text-muted small">
                Chưa có kết luận nào. Agent sẽ tạo kết luận rủi ro chính tại đây.
            </div>
        `;
        return;
    }

    let mainPart = summaryText || "";
    let conclusionPart = conclusionText || "";

    // Nếu conclusionText chưa được backend tách, nhưng summaryText có marker, ta tách phía frontend
    const marker = "### **KẾT LUẬN (CONCLUSION)**";
    if (!conclusionPart && summaryText && summaryText.includes(marker)) {
        const idx = summaryText.indexOf(marker);
        mainPart = summaryText.substring(0, idx).trim();
        conclusionPart = summaryText.substring(idx).trim(); // đã bao gồm heading
    }

    // Render báo cáo chính
    if (mainPart && mainPart.trim()) {
        divSummary.innerHTML = `
            <div class="small" style="white-space: pre-line;">
${mainPart}
            </div>
        `;
    } else {
        divSummary.innerHTML = `
            <div class="text-muted small">
                Chưa có phần báo cáo chi tiết từ agent.
            </div>
        `;
    }

    // Render kết luận
    if (conclusionPart && conclusionPart.trim()) {
        divConclusion.innerHTML = `
            <div class="small" style="white-space: pre-line;">
${conclusionPart}
            </div>
        `;
    } else {
        divConclusion.innerHTML = `
            <div class="text-muted small">
                Agent chưa đưa ra kết luận rõ ràng cho kỳ này.
            </div>
        `;
    }
}

async function initMarketMap() {
    const mapContainer = document.getElementById("map3d");
    if (!mapContainer) return;

    // Nếu map đã init rồi thì không init lại
    if (marketMap && marketMap instanceof L.Map) return;

    // Clear placeholder nếu có
    mapContainer.innerHTML = "";

    // Tạo map 2D vùng Đông Nam Á
    marketMap = L.map("map3d", {
        center: [10, 110], // khoảng trung tâm SEA
        zoom: 4,
        zoomControl: true
    });

    // Base layer: OpenStreetMap
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 8,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(marketMap);

    // Tạo layer groups cho từng overlay mode
    mapLayers = {
        price: L.layerGroup().addTo(marketMap), // mặc định hiển thị price
        weather: L.layerGroup(),
        port: L.layerGroup(),
        warehouse: L.layerGroup(),
        sku: L.layerGroup()
    };
}

function openMapControls() {
    const wrapper = document.getElementById("map-controls-wrapper");
    if (wrapper) {
        wrapper.classList.remove("collapsed");
    }
}

function closeMapControls() {
    const wrapper = document.getElementById("map-controls-wrapper");
    if (wrapper) {
        wrapper.classList.add("collapsed");
    }
}

async function updateMarketData() {
    // Get selected SKUs
    selectedSKUs = Array.from(document.querySelectorAll(".sku-checkbox:checked")).map(cb => cb.value);

    // Fetch market intelligence data
    const skuParam = selectedSKUs.length > 0 ? `?skus=${selectedSKUs.join(",")}` : "";
    const data = await api(`/api/market/intelligence${skuParam}`);

    if (!data) return;

    // Update stats summary
    renderMarketStats(data);

    // Update price table
    renderPriceTable(data.price_data);

    // Update weather table
    renderWeatherTable(data.weather_data);

    // Update map visualization
    updateMapVisualization(data);
}

function renderMarketStats(data) {
    const statsDiv = document.getElementById("market-stats");
    if (!statsDiv) return;

    // Calculate some aggregate stats
    const avgPrices = Object.values(data.price_data).map(d => d.avg_price);
    const avgPrice = (avgPrices.reduce((a,b) => a+b, 0) / avgPrices.length).toFixed(2);

    const totalWarehouses = data.warehouse_data.length;
    const totalCapacity = data.warehouse_data.reduce((sum, w) => sum + w.capacity, 0);
    const totalStock = data.warehouse_data.reduce((sum, w) => sum + w.current_stock, 0);
    const utilizationRate = ((totalStock / totalCapacity) * 100).toFixed(1);

    const avgCongestion = (data.port_data.reduce((sum, p) => sum + p.congestion, 0) / data.port_data.length).toFixed(0);

    statsDiv.innerHTML = `
        <div class="row g-3">
            <div class="col-md-3">
                <div class="market-stat-card">
                    <i class="fas fa-dollar-sign fa-2x mb-2"></i>
                    <div class="market-stat-label">Avg Market Price</div>
                    <div class="market-stat-value">$${avgPrice}</div>
                    <div class="market-stat-change"><i class="fas fa-arrow-up me-1"></i>+3.2% vs last week</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="market-stat-card" style="background:linear-gradient(135deg,#198754 0%,#146c43 100%)">
                    <i class="fas fa-warehouse fa-2x mb-2"></i>
                    <div class="market-stat-label">Warehouse Utilization</div>
                    <div class="market-stat-value">${utilizationRate}%</div>
                    <div class="market-stat-change">${totalWarehouses} facilities | ${(totalCapacity/1000).toFixed(0)}K capacity</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="market-stat-card" style="background:linear-gradient(135deg,#dc3545 0%,#b02a37 100%)">
                    <i class="fas fa-ship fa-2x mb-2"></i>
                    <div class="market-stat-label">Avg Port Congestion</div>
                    <div class="market-stat-value">${avgCongestion}%</div>
                    <div class="market-stat-change">${data.port_data.length} major ports monitored</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="market-stat-card" style="background:linear-gradient(135deg,#ffc107 0%,#cc9a06 100%)">
                    <i class="fas fa-box fa-2x mb-2"></i>
                    <div class="market-stat-label">SKUs Analyzed</div>
                    <div class="market-stat-value">${selectedSKUs.length || 'All'}</div>
                    <div class="market-stat-change">Real-time market insights</div>
                </div>
            </div>
        </div>
    `;
}

function renderPriceTable(priceData) {
    const tableDiv = document.getElementById("price-table");
    if (!tableDiv) return;

    tableDiv.innerHTML = `
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Region</th>
                        <th>Avg Price</th>
                        <th>Competitor</th>
                        <th>Trend</th>
                        <th>Market Share</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(priceData).map(([region, data]) => `
                        <tr>
                            <td><strong>${region}</strong></td>
                            <td>$${data.avg_price}</td>
                            <td>$${data.competitor_price}</td>
                            <td>
                                <i class="fas fa-arrow-${data.price_trend === 'up' ? 'up text-danger' : data.price_trend === 'down' ? 'down text-success' : 'right text-secondary'}"></i>
                                ${data.price_trend}
                            </td>
                            <td><span class="badge bg-${data.market_share > 30 ? 'success' : data.market_share > 20 ? 'warning' : 'secondary'}">${data.market_share}%</span></td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function renderWeatherTable(weatherData) {
    const tableDiv = document.getElementById("weather-table");
    if (!tableDiv) return;

    const weatherIcons = {
        sunny: "sun text-warning",
        rainy: "cloud-rain text-primary",
        cloudy: "cloud text-secondary",
        stormy: "bolt text-danger",
        hazy: "smog text-muted"
    };

    tableDiv.innerHTML = `
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Region</th>
                        <th>Condition</th>
                        <th>Temp (°C)</th>
                        <th>Humidity</th>
                        <th>Impact</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(weatherData).map(([region, data]) => `
                        <tr>
                            <td><strong>${region}</strong></td>
                            <td><i class="fas fa-${weatherIcons[data.condition] || 'cloud'}"></i> ${data.condition}</td>
                            <td>${data.temperature}°C</td>
                            <td>${data.humidity}%</td>
                            <td><span class="badge bg-${data.impact_score > 1.2 ? 'success' : data.impact_score < 0.8 ? 'danger' : 'secondary'}">${data.impact_score}x</span></td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function updateMapVisualization(data) {
    if (!marketMap || !(marketMap instanceof L.Map)) return;

    // Xóa markers cũ & remove tất cả overlay layers khỏi map
    Object.values(mapLayers).forEach(layer => {
        if (marketMap.hasLayer(layer)) {
            marketMap.removeLayer(layer);
        }
        layer.clearLayers();
    });

    // Lấy layer active theo mode
    const activeLayer = mapLayers[currentMapMode] || mapLayers.price;

    // 1) PRICE OVERLAY (data.price_data từ DB)
    if (currentMapMode === "price") {
        Object.entries(data.price_data).forEach(([region, d]) => {
            const coords = REGION_COORDS_FRONT[region];
            if (!coords) return;

            const price = d.avg_price;
            const color =
                price > 20 ? "#dc3545" :   // cao
                price > 15 ? "#ffc107" :   // trung bình
                             "#198754";    // thấp

            L.circleMarker(coords, {
                radius: 10,
                color,
                fillColor: color,
                fillOpacity: 0.7
            }).bindPopup(`
                <strong>${region}</strong><br>
                Avg price: $${price}<br>
                Competitor: $${d.competitor_price}<br>
                Market share: ${d.market_share}%
            `).addTo(activeLayer);
        });

    // 2) WEATHER OVERLAY (data.weather_data – giống bảng Weather Impact)
    } else if (currentMapMode === "weather") {
        Object.entries(data.weather_data).forEach(([region, d]) => {
            const coords = REGION_COORDS_FRONT[region];
            if (!coords) return;

            const impact = d.impact_score;
            // Đồng bộ logic với bảng: >1.2 xanh, <0.8 đỏ, còn lại xám
            const color =
                impact > 1.2 ? "#198754" :   // good impact (bg-success)
                impact < 0.8 ? "#dc3545" :   // bad (bg-danger)
                               "#6c757d";    // neutral (bg-secondary)

            L.circleMarker(coords, {
                radius: 10,
                color,
                fillColor: color,
                fillOpacity: 0.7
            }).bindPopup(`
                <strong>${region}</strong><br>
                Condition: ${d.condition}<br>
                Temp: ${d.temperature}°C<br>
                Humidity: ${d.humidity}%<br>
                Impact: ${impact}x
            `).addTo(activeLayer);
        });

    // 3) PORT & LOGISTICS OVERLAY (sea + road)
    } else if (currentMapMode === "port") {
        // SEA logistics: port_data (DB)
        data.port_data.forEach(p => {
            const coords = (p.lat != null && p.lng != null)
                ? [p.lat, p.lng]                // <-- dùng 'lng' đúng field backend
                : REGION_COORDS_FRONT[p.region || p.country];

            if (!coords) return;

            const cong = p.congestion;
            const color =
                cong > 70 ? "#dc3545" :   // nặng
                cong > 40 ? "#ffc107" :   // trung bình
                            "#198754";    // nhẹ

            L.circleMarker(coords, {
                radius: 9,
                color,
                fillColor: color,
                fillOpacity: 0.7
            }).bindPopup(`
                <strong>${p.name}</strong><br>
                Region: ${p.region || "-"}<br>
                Congestion: ${cong}%<br>
                Delay: ${p.delay_days} days
            `).addTo(activeLayer);
        });

        // ROAD logistics demo: tuyến VN–TH–MY–SG
        const corridorCoords = [
            REGION_COORDS_FRONT["Vietnam"],
            REGION_COORDS_FRONT["Thailand"],
            REGION_COORDS_FRONT["Malaysia"],
            REGION_COORDS_FRONT["Singapore"]
        ].filter(Boolean);

        if (corridorCoords.length >= 2) {
            L.polyline(corridorCoords, {
                weight: 3,
                opacity: 0.6
            }).addTo(activeLayer);
        }

    // 4) WAREHOUSE OVERLAY (warehouse_data từ DB)
    } else if (currentMapMode === "warehouse") {
        data.warehouse_data.forEach(w => {
            const coords = (w.lat != null && w.lng != null)
                ? [w.lat, w.lng]
                : REGION_COORDS_FRONT[w.region];
            if (!coords) return;

            const util = (w.current_stock / w.capacity) * 100;
            const color =
                util > 85 ? "#dc3545" :   // critical
                util > 65 ? "#ffc107" :   // optimal
                            "#198754";    // good

            L.circleMarker(coords, {
                radius: 9,
                color,
                fillColor: color,
                fillOpacity: 0.7
            }).bindPopup(`
                <strong>${w.name || "Warehouse"}</strong><br>
                Region: ${w.region}<br>
                Utilization: ${util.toFixed(0)}%<br>
                Stock: ${w.current_stock} / ${w.capacity}
            `).addTo(activeLayer);
        });

    // 5) SKU OVERLAY (nếu bạn cần)
    } else if (currentMapMode === "sku") {
        Object.entries(data.price_data).forEach(([region, d]) => {
            const coords = REGION_COORDS_FRONT[region];
            if (!coords) return;

            const demand = d.market_share; // proxy demand
            const color =
                demand > 35 ? "#0d6efd" :   // high demand
                demand > 20 ? "#198754" :   // steady
                              "#dc3545";    // low

            L.circleMarker(coords, {
                radius: 9,
                color,
                fillColor: color,
                fillOpacity: 0.7
            }).bindPopup(`
                <strong>${region}</strong><br>
                Demand (proxy: market share): ${d.market_share}%<br>
                Avg price: $${d.avg_price}
            `).addTo(activeLayer);
        });
    }

    // Add overlay đang active lên map
    activeLayer.addTo(marketMap);

    // Legend UI
    updateMapLegend();
}

function changeMapMode(mode) {
    currentMapMode = mode;

    // Update button states
    document.querySelectorAll(".map-mode-btn").forEach(btn => btn.classList.remove("active"));
    document.getElementById(`btn-mode-${mode}`)?.classList.add("active");

    // Refresh data
    updateMarketData();
}

function updateMapLegend() {
    const legendContent = document.getElementById("legend-content");
    if (!legendContent) return;

    const legends = {
        price: [
            { color: "#198754", label: "Low ($8-15)" },
            { color: "#ffc107", label: "Medium ($15-20)" },
            { color: "#dc3545", label: "High ($20+)" }
        ],
        weather: [
            { color: "#ffc107", label: "Sunny" },
            { color: "#0d6efd", label: "Rainy" },
            { color: "#6c757d", label: "Cloudy" },
            { color: "#dc3545", label: "Stormy" }
        ],
        port: [
            { color: "#198754", label: "Low Congestion (0-40%)" },
            { color: "#ffc107", label: "Medium (40-70%)" },
            { color: "#dc3545", label: "High (70%+)" }
        ],
        warehouse: [
            { color: "#198754", label: "Good (<65%)" },
            { color: "#ffc107", label: "Optimal (65-85%)" },
            { color: "#dc3545", label: "Critical (85%+)" }
        ],
        sku: [
            { color: "#0d6efd", label: "High Demand" },
            { color: "#198754", label: "Steady" },
            { color: "#dc3545", label: "Low Stock" }
        ]
    };

    const currentLegend = legends[currentMapMode] || legends.price;
    legendContent.innerHTML = currentLegend.map(item => `
        <div class="legend-item">
            <div class="legend-color" style="background:${item.color}"></div>
            <span>${item.label}</span>
        </div>
    `).join("");
}

async function refreshMarketData() {
    await updateMarketData();
    alert("✓ Market data refreshed!");
}

// ========== CHART RENDERING HELPERS ==========

function renderFanChart(fanData) {
    const ctx = document.getElementById("fanChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "line",
        data: {
            labels: fanData.labels,
            datasets: [
                {
                    label: "P90",
                    data: fanData.p90,
                    borderColor: "rgba(220, 53, 69, 0.5)",
                    backgroundColor: "rgba(220, 53, 69, 0.1)",
                    fill: "+1"
                },
                {
                    label: "P50",
                    data: fanData.p50,
                    borderColor: "rgb(13, 110, 253)",
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: "P10",
                    data: fanData.p10,
                    borderColor: "rgba(25, 135, 84, 0.5)",
                    backgroundColor: "rgba(25, 135, 84, 0.1)",
                    fill: "-1"
                },
                {
                    label: "Actual",
                    data: [...fanData.actual, ...Array(fanData.labels.length - fanData.actual.length).fill(null)],
                    borderColor: "rgb(255, 193, 7)",
                    borderWidth: 2,
                    pointRadius: 2,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { position: "top" },
                tooltip: { mode: "index" }
            }
        }
    });
}

function renderCategoryChart(categoryData) {
    const ctx = document.getElementById("categoryChart");
    if (!ctx) return;

    const categories = Object.keys(categoryData).filter(k => k !== "labels");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: categoryData.labels,
            datasets: categories.map((cat, i) => ({
                label: cat,
                data: categoryData[cat],
                borderColor: `hsl(${i * 80}, 70%, 50%)`,
                fill: false
            }))
        },
        options: {
            responsive: true,
            plugins: { legend: { position: "top" } }
        }
    });
}

function renderSKUFanChart(fanData) {
    const ctx = document.getElementById("skuFanChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "line",
        data: {
            labels: fanData.labels,
            datasets: [
                { label: "P90", data: fanData.p90, borderColor: "rgba(220, 53, 69, 0.7)", fill: false },
                { label: "P50", data: fanData.p50, borderColor: "rgb(13, 110, 253)", fill: false },
                { label: "P10", data: fanData.p10, borderColor: "rgba(25, 135, 84, 0.7)", fill: false },
                { label: "Actual", data: [...fanData.actual, ...Array(fanData.labels.length - fanData.actual.length).fill(null)], borderColor: "rgb(255, 193, 7)", fill: false }
            ]
        },
        options: { responsive: true }
    });
}

function renderComponentsChart(components) {
    const ctx = document.getElementById("componentsChart");
    if (!ctx) return;

    const labels = Array.from({ length: components.trend.length }, (_, i) => `D${i + 1}`);
    new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                { label: "Trend", data: components.trend, borderColor: "rgb(13, 110, 253)", fill: false },
                { label: "Weekly", data: components.weekly, borderColor: "rgb(25, 135, 84)", fill: false },
                { label: "Yearly", data: components.yearly, borderColor: "rgb(255, 193, 7)", fill: false },
                { label: "Holidays", data: components.holidays, borderColor: "rgb(220, 53, 69)", fill: false }
            ]
        },
        options: { responsive: true }
    });
}

function renderSHAPChart(shapData) {
    const ctx = document.getElementById("shapChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: shapData.map(s => s.feature),
            datasets: [{
                label: "Importance",
                data: shapData.map(s => s.importance),
                backgroundColor: "rgba(13, 110, 253, 0.7)"
            }]
        },
        options: { indexAxis: "y", responsive: true }
    });
}
function onSkuSelectChange(skuCode) {
    renderForecastSKU(skuCode);
}
// ========== ACTION FUNCTIONS ==========
function handleAlertClick(event, link) {
    event.preventDefault();

    switch (link) {
        case "/forecast/sku":
            navigate("B", "sku");
            break;
        case "/forecast/backtest":
            navigate("B", "backtest");
            break;
        case "/dashboard":
            navigate("A", "overview");
            break;
        case "/monitoring":
            navigate("D", "monitoring");
            break;
        case "/data/exogenous":
            navigate("D", "exogenous");
            break;
        default:
            // fallback: về dashboard overview
            navigate("A", "overview");
    }
}

async function setChampion(model) {
    const sku = DENSO_SKUS[0].code;
    const result = await api("/api/models/set_champion", {
        method: "POST",
        body: JSON.stringify({ sku, model })
    });
    if (result && result.ok) {
        alert(`✓ ${result.message}`);
    }
}

async function updateScenario() {
    const priceDelta = parseFloat(document.getElementById("price-delta").value);
    const promoDepth = parseFloat(document.getElementById("promo-depth").value);
    const adSpend = parseFloat(document.getElementById("ad-spend").value);

    document.getElementById("price-delta-val").textContent = `${priceDelta}%`;
    document.getElementById("promo-depth-val").textContent = `${(promoDepth * 100).toFixed(0)}%`;
    document.getElementById("ad-spend-val").textContent = `${adSpend}x`;

    const result = await api("/api/scenario/whatif", {
        method: "POST",
        body: JSON.stringify({ price_delta: priceDelta, promo_depth: promoDepth, ad_spend: adSpend })
    });

    if (result) {
        document.getElementById("scenario-result").textContent = `$${result.forecast}`;
    }
}
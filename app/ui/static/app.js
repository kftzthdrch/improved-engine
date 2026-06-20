// ── Vehicle ID ─────────────────────────────────────────────
function vid() { return document.getElementById('vehicleId').value.trim() || 'VH-001'; }

// ── Toast Notifications ────────────────────────────────────
function toast(msg, type = 'info') {
    const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span class="toast-icon">${icons[type] ?? 'ℹ'}</span><span>${msg}</span>`;
    document.getElementById('toasts').prepend(el);
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add('toast-show')));
    setTimeout(() => {
        el.classList.remove('toast-show');
        el.classList.add('toast-hide');
        el.addEventListener('transitionend', () => el.remove(), { once: true });
    }, 3500);
}

// ── API Wrapper ────────────────────────────────────────────
async function api(method, path, body) {
    try {
        const res = await fetch(path, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: body !== undefined ? JSON.stringify(body) : undefined,
        });
        const data = await res.json().catch(() => ({}));
        return { ok: res.ok, status: res.status, data };
    } catch (e) {
        return { ok: false, status: 0, data: { error: { message: e.message } } };
    }
}

// ── Button Loading ─────────────────────────────────────────
function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) {
        btn.disabled = true;
        btn.dataset.orig = btn.innerHTML;
        btn.innerHTML = '…';
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.orig ?? btn.innerHTML;
    }
}

// ── Vitals Strip ───────────────────────────────────────────
function updateVitals(snap) {
    const bat = snap.battery_percent;

    document.getElementById('vBattery').textContent = `${bat}%`;
    document.getElementById('vSpeed').textContent   = `${snap.speed_kph} km/h`;
    document.getElementById('vOdometer').textContent = `${snap.odometer_km.toLocaleString()} km`;
    document.getElementById('vDoor').textContent     = snap.door_locked ? 'Locked' : 'Unlocked';
    document.getElementById('doorIcon').textContent  = snap.door_locked ? '🔒' : '🔓';
    document.getElementById('vCabin').textContent    = `${snap.cabin_temperature_c}°C`;
    document.getElementById('vTime').textContent     = new Date(snap.timestamp).toLocaleTimeString();

    const fill = document.getElementById('batteryFill');
    fill.style.width      = `${bat}%`;
    fill.style.background = bat < 20 ? '#dc2626' : bat < 50 ? '#d97706' : '#16a34a';

    const badge = document.getElementById('connBadge');
    badge.textContent = 'Live';
    badge.classList.add('connected');
}

// ── Telemetry ──────────────────────────────────────────────
async function submitTelemetry(btn) {
    setLoading(btn, true);
    const r = await api('POST', `/vehicles/${vid()}/telemetry`, {
        speed_kph:          parseFloat(document.getElementById('speed').value),
        battery_percent:    parseFloat(document.getElementById('battery').value),
        odometer_km:        parseFloat(document.getElementById('odometer').value),
        door_locked:        document.getElementById('doorLocked').checked,
        cabin_temperature_c: parseFloat(document.getElementById('cabinTemp').value),
    });
    setLoading(btn, false);
    if (r.ok) {
        updateVitals(r.data);
        toast('Telemetry submitted', 'success');
        loadEligibility();
    } else {
        toast(r.data?.error?.message ?? 'Failed to submit telemetry', 'error');
    }
}

function updateDoorLabel() {
    const locked = document.getElementById('doorLocked').checked;
    document.getElementById('doorLabel').textContent = locked ? 'Locked' : 'Unlocked';
}

// ── Refresh All ────────────────────────────────────────────
async function refreshAll() {
    const r = await api('GET', `/vehicles/${vid()}/status`);
    if (r.ok) updateVitals(r.data);
    await Promise.all([loadEligibility(), loadAlerts(), loadMaintenance(), loadDiagnostics()]);
}

// ── Commands ───────────────────────────────────────────────
async function sendCmd(path) {
    const r = await api('POST', `/vehicles/${vid()}/commands/${path}`);
    handleCmdResult(r);
}

async function setTemperature() {
    const temp = parseFloat(document.getElementById('targetTemp').value);
    const r = await api('POST', `/vehicles/${vid()}/commands/climate/temperature`, { target_celsius: temp });
    handleCmdResult(r);
}

function handleCmdResult(r) {
    if (!r.ok) {
        toast(r.data?.error?.message ?? 'Command failed', r.status === 409 ? 'warning' : 'error');
        return;
    }
    const { command_type: type, status, failure_reason: reason } = r.data;
    const label = (type ?? '').replace(/_/g, ' ');
    if (status === 'SUCCEEDED')  toast(`${label} succeeded`, 'success');
    else if (status === 'REJECTED') toast(`${label} rejected: ${reason}`, 'warning');
    else if (status === 'FAILED')   toast(`${label} failed: ${reason}`, 'error');
    else toast(`${label}: ${status}`, 'info');
}

// ── Eligibility ────────────────────────────────────────────
async function loadEligibility() {
    const r = await api('GET', `/vehicles/${vid()}/commands/eligibility`);
    const el = document.getElementById('eligibilityOutput');
    if (!r.ok) {
        el.innerHTML = '<p class="empty">Could not load eligibility.</p>';
        return;
    }
    el.innerHTML = (r.data.eligibility ?? []).map(item => `
        <div class="elig-item ${item.allowed ? 'elig-allowed' : 'elig-blocked'}">
            <span class="elig-icon">${item.allowed ? '✓' : '✗'}</span>
            <div class="elig-body">
                <span class="elig-name">${item.command_type.replace(/_/g, ' ')}</span>
                ${!item.allowed && item.reason ? `<span class="elig-reason">${item.reason}</span>` : ''}
            </div>
        </div>
    `).join('');
}

// ── Alerts ─────────────────────────────────────────────────
async function loadAlerts() {
    const r = await api('GET', `/vehicles/${vid()}/alerts`);
    const el    = document.getElementById('alertsOutput');
    const badge = document.getElementById('alertCount');
    if (!r.ok) { el.innerHTML = '<p class="empty">Could not load alerts.</p>'; return; }

    const alerts = r.data;
    if (!alerts.length) {
        el.innerHTML = '<div class="no-issues">✓ No active alerts</div>';
        badge.style.display = 'none';
        return;
    }
    badge.textContent   = alerts.length;
    badge.style.display = 'inline-flex';
    el.innerHTML = alerts.map(a => `
        <div class="alert-item">
            <div class="alert-dot"></div>
            <div class="alert-body">
                <div class="alert-type">${a.alert_type.replace(/_/g, ' ')}</div>
                <div class="alert-msg">${a.message}</div>
            </div>
            <button class="alert-clear" onclick="clearAlert('${a.alert_type}')">Clear</button>
        </div>
    `).join('');
}

async function clearAlert(type) {
    const r = await api('DELETE', `/vehicles/${vid()}/alerts/${type}`);
    if (r.ok) { toast('Alert cleared', 'success'); loadAlerts(); }
    else toast(r.data?.error?.message ?? 'Failed to clear alert', 'error');
}

// ── Trips ──────────────────────────────────────────────────
async function startTrip() {
    const r = await api('POST', `/vehicles/${vid()}/trips/start`);
    if (r.ok) { toast('Trip started', 'success'); renderTrip(r.data); }
    else toast(r.data?.error?.message ?? 'Cannot start trip', 'error');
}

async function endTrip() {
    const r = await api('POST', `/vehicles/${vid()}/trips/end`);
    if (r.ok) { toast('Trip ended', 'success'); renderTrip(r.data); }
    else toast(r.data?.error?.message ?? 'Cannot end trip', 'error');
}

async function loadCurrentTrip() {
    const r = await api('GET', `/vehicles/${vid()}/trips/current`);
    if (r.ok) renderTrip(r.data);
    else toast(r.data?.error?.message ?? 'No active trip', 'warning');
}

async function loadTripSummary() {
    const r = await api('GET', `/vehicles/${vid()}/trips/latest-summary`);
    if (r.ok) renderTrip(r.data);
    else toast(r.data?.error?.message ?? 'No completed trips found', 'warning');
}

function renderTrip(trip) {
    const el = document.getElementById('tripOutput');
    const isActive = trip.status === 'ACTIVE';
    const dist = trip.distance_km != null ? trip.distance_km.toFixed(1) : null;
    el.innerHTML = `
        <div class="trip-status-row">
            <span class="trip-badge ${isActive ? 'trip-active' : 'trip-completed'}">${trip.status}</span>
            <span class="trip-id">${trip.id.slice(0, 8)}…</span>
        </div>
        <div class="trip-rows">
            <div class="trip-row">
                <span>Started</span>
                <strong>${new Date(trip.started_at).toLocaleString()}</strong>
            </div>
            ${trip.ended_at ? `
            <div class="trip-row">
                <span>Ended</span>
                <strong>${new Date(trip.ended_at).toLocaleString()}</strong>
            </div>` : ''}
            <div class="trip-row">
                <span>Start odometer</span>
                <strong>${trip.start_odometer_km.toLocaleString()} km</strong>
            </div>
            ${trip.end_odometer_km != null ? `
            <div class="trip-row">
                <span>End odometer</span>
                <strong>${trip.end_odometer_km.toLocaleString()} km</strong>
            </div>` : ''}
        </div>
        ${dist !== null ? `
        <div class="trip-distance">
            <strong>${dist}</strong>
            <span>km driven</span>
        </div>` : ''}
    `;
}

// ── Maintenance ────────────────────────────────────────────
async function loadMaintenance() {
    const r = await api('GET', `/vehicles/${vid()}/maintenance`);
    if (r.ok) renderMaintenance(r.data);
    else toast('Could not load maintenance data', 'error');
}

async function resetService() {
    const r = await api('POST', `/vehicles/${vid()}/maintenance/service-reset`);
    if (r.ok) { toast('Service reset recorded', 'success'); renderMaintenance(r.data); }
    else toast('Failed to reset service', 'error');
}

function renderMaintenance(data) {
    const el = document.getElementById('maintenanceOutput');
    el.innerHTML = `
        <div class="maint-row">
            <span>Oil / Service</span>
            <span class="maint-badge ${data.service_due ? 'badge-due' : 'badge-ok'}">
                ${data.service_due ? 'Due' : 'OK'}
            </span>
        </div>
        <div class="maint-row">
            <span>Tire Check</span>
            <span class="maint-badge ${data.tire_check_due ? 'badge-due' : 'badge-ok'}">
                ${data.tire_check_due ? 'Due' : 'OK'}
            </span>
        </div>
        <div class="maint-meta">
            <div class="maint-detail">
                <span>Current odometer</span>
                <strong>${data.current_odometer_km.toLocaleString()} km</strong>
            </div>
            <div class="maint-detail">
                <span>Last service at</span>
                <strong>${data.last_service_odometer_km.toLocaleString()} km</strong>
            </div>
            <div class="maint-detail">
                <span>Last tire check at</span>
                <strong>${data.last_tire_check_odometer_km.toLocaleString()} km</strong>
            </div>
        </div>
    `;
}

// ── Diagnostics ────────────────────────────────────────────
async function submitDemodiagnostics() {
    const r = await api('POST', `/vehicles/${vid()}/diagnostics`, {
        codes: [
            { code: 'P0128', severity: 'WARNING', description: 'Coolant temperature below thermostat regulating temperature' },
            { code: 'B1001', severity: 'INFO',    description: 'Cabin sensor unavailable' },
            { code: 'U0100', severity: 'ERROR',   description: 'Lost communication with ECM' },
        ],
    });
    if (r.ok) { toast(`${r.data.length} diagnostic code(s) submitted`, 'success'); loadDiagnostics(); }
    else toast('Failed to submit diagnostic codes', 'error');
}

async function loadDiagnostics() {
    const r = await api('GET', `/vehicles/${vid()}/diagnostics`);
    const el    = document.getElementById('diagnosticsOutput');
    const badge = document.getElementById('diagCount');
    if (!r.ok) { el.innerHTML = '<p class="empty">Could not load diagnostics.</p>'; return; }

    const codes = r.data;
    if (!codes.length) {
        el.innerHTML = '<div class="no-issues">✓ No active codes</div>';
        badge.style.display = 'none';
        return;
    }
    badge.textContent   = codes.length;
    badge.style.display = 'inline-flex';

    const order = { CRITICAL: 0, ERROR: 1, WARNING: 2, INFO: 3 };
    codes.sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9));

    el.innerHTML = codes.map(d => `
        <div class="diag-item diag-${d.severity.toLowerCase()}">
            <span class="diag-sev">${d.severity.slice(0, 4)}</span>
            <div class="diag-body">
                <div class="diag-code">${d.code}</div>
                <div class="diag-desc">${d.description}</div>
            </div>
            <button class="diag-clear" onclick="clearDiagnostic('${d.code}')">Clear</button>
        </div>
    `).join('');
}

async function clearDiagnostic(code) {
    const r = await api('DELETE', `/vehicles/${vid()}/diagnostics/${code}`);
    if (r.ok) { toast(`Code ${code} cleared`, 'success'); loadDiagnostics(); }
    else toast(`Failed to clear ${code}`, 'error');
}

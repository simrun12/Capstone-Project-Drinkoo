/**
 * DRINKOO client-side telemetry.
 *
 * - Generates a session id per browser tab (sessionStorage scoped).
 * - Captures clicks on tagged elements, page views, fetch failures, and JS errors.
 * - Polls /observability/status to drive the live status indicator pill.
 * - Sends events only when the user is authenticated; never reads other users'
 *   logs (the server enforces admin-only access for log queries).
 */

const TELEMETRY_API = (typeof API_BASE_URL !== 'undefined')
    ? API_BASE_URL
    : 'http://localhost:8000/api/v1';

const SESSION_KEY = 'drinkoo_session_id';

function getSessionId() {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
        id = 'sess_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
        sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
}

const TELEMETRY_QUEUE = [];
let flushScheduled = false;

function scheduleFlush() {
    if (flushScheduled) return;
    flushScheduled = true;
    setTimeout(flushTelemetry, 1500);
}

async function flushTelemetry() {
    flushScheduled = false;
    if (TELEMETRY_QUEUE.length === 0) return;
    const token = (typeof getAuthToken === 'function') ? getAuthToken() : null;
    if (!token) {
        // Drop queued events if user is not signed in (status pill still works).
        TELEMETRY_QUEUE.length = 0;
        return;
    }
    const batch = TELEMETRY_QUEUE.splice(0, TELEMETRY_QUEUE.length);
    for (const event of batch) {
        try {
            await fetch(`${TELEMETRY_API}/observability/frontend-event`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'X-Session-Id': getSessionId(),
                },
                body: JSON.stringify(event),
                keepalive: true,
            });
        } catch (_) {
            // Swallow — telemetry must never break the UI.
        }
    }
}

function trackEvent(eventType, category, options = {}) {
    TELEMETRY_QUEUE.push({
        event_type: eventType,
        category: category,
        severity: options.severity || 'info',
        session_id: getSessionId(),
        path: options.path || window.location.pathname,
        success: options.success,
        duration_ms: options.durationMs,
        details: options.details || null,
    });
    scheduleFlush();
}

// Expose helpers globally
window.trackEvent = trackEvent;
window.getSessionId = getSessionId;

// ---------- Automatic capture ----------

window.addEventListener('DOMContentLoaded', () => {
    trackEvent('page_view', 'navigation', {
        details: { title: document.title, referrer: document.referrer || null },
    });

    // Capture clicks on elements explicitly tagged for telemetry, or interactive elements.
    document.body.addEventListener('click', (event) => {
        const target = event.target.closest('[data-track], button, a, .nav-link');
        if (!target) return;
        const label = target.getAttribute('data-track')
            || target.getAttribute('aria-label')
            || (target.innerText || '').trim().slice(0, 60)
            || target.tagName;
        trackEvent('click', 'interaction', {
            details: {
                label,
                tag: target.tagName,
                view: target.closest('[data-view]')?.getAttribute('data-view') || null,
            },
        });
    }, true);
});

window.addEventListener('error', (event) => {
    trackEvent('js_error', 'frontend_error', {
        severity: 'error',
        success: false,
        details: {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
        },
    });
});

window.addEventListener('unhandledrejection', (event) => {
    trackEvent('promise_rejection', 'frontend_error', {
        severity: 'error',
        success: false,
        details: { reason: String(event.reason).slice(0, 500) },
    });
});

// Flush on page hide for last-mile delivery
window.addEventListener('pagehide', () => {
    flushTelemetry();
});

// ---------- Status indicator ----------

async function refreshStatus() {
    const pill = document.getElementById('drinkooStatusPill');
    if (!pill) return;
    try {
        const res = await fetch(`${TELEMETRY_API}/observability/status`);
        if (!res.ok) throw new Error('status_unreachable');
        const data = await res.json();
        const status = data.status || 'unknown';
        pill.dataset.status = status;
        const label = pill.querySelector('.status-label');
        if (label) {
            label.textContent = status === 'online' ? 'Online'
                : status === 'degraded' ? 'Degraded'
                : 'Unknown';
        }
    } catch (_) {
        pill.dataset.status = 'offline';
        const label = pill.querySelector('.status-label');
        if (label) label.textContent = 'Offline';
    }
}

function injectStatusPill() {
    if (document.getElementById('drinkooStatusPill')) return;
    const pill = document.createElement('div');
    pill.id = 'drinkooStatusPill';
    pill.className = 'status-pill';
    pill.dataset.status = 'unknown';
    pill.innerHTML = '<span class="status-dot"></span><span class="status-label">Checking…</span>';
    document.body.appendChild(pill);
}

window.addEventListener('DOMContentLoaded', () => {
    injectStatusPill();
    refreshStatus();
    setInterval(refreshStatus, 15000);
});

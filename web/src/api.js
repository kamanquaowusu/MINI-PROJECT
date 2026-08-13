// VITE_API_BASE lets a later deployment point at a hosted API without any
// code change; '' (the dev default) relies on Vite's /api proxy so the
// browser sees same-origin requests and CORS never comes up locally.
const BASE = import.meta.env.VITE_API_BASE ?? '';

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export function checkMessage({ message, consent }) {
  return request('/api/check', {
    method: 'POST',
    body: JSON.stringify({ message, consent_to_log: consent }),
  });
}

export function sendFeedback({ checkId, verdict, note }) {
  return request('/api/feedback', {
    method: 'POST',
    body: JSON.stringify({ check_id: checkId, verdict, note: note ?? null }),
  });
}

export function fetchHealth() {
  return request('/api/health', { method: 'GET' });
}

export function submitReport({ message, phone, email, checkId }) {
  return request('/api/report', {
    method: 'POST',
    body: JSON.stringify({
      message,
      phone: phone || null,
      email: email || null,
      check_id: checkId ?? null,
    }),
  });
}

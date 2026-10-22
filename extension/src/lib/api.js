/**
 * Background API Client for CIF Chrome Extension (Step 8.2 & Step 8.7).
 * Executes all network calls inside the service worker.
 * Never leaks tokens, enforces origin allowlist and timeouts.
 */

export const DEFAULT_BASE_URL = 'http://127.0.0.1:8080';
export const ALLOWED_ORIGINS = [
  'http://127.0.0.1:8080',
  'http://localhost:8080'
];

export async function getBackendBaseUrl() {
  if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
    const data = await chrome.storage.local.get(['cif_backend_url']);
    const custom = data.cif_backend_url;
    if (custom && ALLOWED_ORIGINS.includes(custom)) {
      return custom;
    }
  }
  return DEFAULT_BASE_URL;
}

export async function getSessionToken() {
  if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
    const data = await chrome.storage.local.get(['cif_session_token', 'cif_token_expires_at']);
    if (data.cif_session_token) {
      if (data.cif_token_expires_at && Date.now() > data.cif_token_expires_at) {
        await chrome.storage.local.remove(['cif_session_token', 'cif_token_expires_at', 'cif_user']);
        return null;
      }
      return data.cif_session_token;
    }
  }
  return null;
}

export async function apiRequest(endpoint, options = {}) {
  const baseUrl = await getBackendBaseUrl();
  const token = await getSessionToken();

  const url = `${baseUrl.replace(/\/+$/, '')}/${endpoint.replace(/^\/+/, '')}`;
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {})
  };

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeoutMs = options.timeoutMs || 25000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal
    });
    clearTimeout(timer);

    let json;
    try {
      json = await res.json();
    } catch (e) {
      json = { status: 'error', message: `Invalid response format HTTP ${res.status}` };
    }

    if (res.status === 401) {
      // Token expired or invalid
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        await chrome.storage.local.remove(['cif_session_token', 'cif_token_expires_at', 'cif_user']);
      }
      return { ...json, status: 'needs_relogin', status_code: 401 };
    }

    return json;
  } catch (err) {
    clearTimeout(timer);
    return {
      status: 'error',
      message: err.name === 'AbortError' ? 'Request timed out' : `Connection error: ${err.message}`
    };
  }
}

// CommonJS support for Node.js / Python runner tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { DEFAULT_BASE_URL, ALLOWED_ORIGINS, getBackendBaseUrl, getSessionToken, apiRequest };
}

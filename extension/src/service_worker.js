/**
 * CIF Chrome Extension - Background Service Worker (Manifest V3)
 * Handles all network requests, authentication flows, and storage.
 * Enforces sender validation (sender.id === chrome.runtime.id) and typed messages.
 */

import { MessageTypes, validateMessage } from './lib/messages.js';
import { apiRequest, getBackendBaseUrl, getSessionToken } from './lib/api.js';

// --- Authentication Workflows (Step 8.2) ---

async function signIn() {
  const baseUrl = await getBackendBaseUrl();
  const extId = chrome.runtime.id;
  const authUrl = `${baseUrl.replace(/\/+$/, '')}/auth/github/login?client=extension&ext_id=${encodeURIComponent(extId)}`;

  return new Promise((resolve) => {
    chrome.identity.launchWebAuthFlow({
      url: authUrl,
      interactive: true
    }, async (redirectUrl) => {
      if (chrome.runtime.lastError || !redirectUrl) {
        resolve({
          status: 'error',
          message: chrome.runtime.lastError ? chrome.runtime.lastError.message : 'User cancelled sign-in'
        });
        return;
      }

      try {
        const parsed = new URL(redirectUrl);
        const code = parsed.searchParams.get('code');
        if (!code) {
          resolve({ status: 'error', message: 'No authorization code returned from GitHub flow' });
          return;
        }

        // Exchange one-time code for CIF session token
        const exchangeRes = await apiRequest('auth/extension/exchange', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code })
        });

        if (exchangeRes && exchangeRes.status === 'success' && exchangeRes.session_token) {
          const expiresAt = Date.now() + (7 * 24 * 60 * 60 * 1000); // 7-day sliding expiry
          await chrome.storage.local.set({
            cif_session_token: exchangeRes.session_token,
            cif_token_expires_at: expiresAt,
            cif_user: exchangeRes.user || null
          });

          // Fetch fresh profile
          const meRes = await apiRequest('api/me');
          if (meRes && meRes.status === 'success') {
            await chrome.storage.local.set({ cif_user: meRes });
          }

          resolve({ status: 'success', user: exchangeRes.user });
        } else {
          resolve({
            status: 'error',
            message: exchangeRes ? exchangeRes.message : 'Token exchange failed'
          });
        }
      } catch (err) {
        resolve({ status: 'error', message: `Sign-in processing error: ${err.message}` });
      }
    });
  });
}

async function signOut() {
  try {
    await apiRequest('auth/logout', { method: 'POST' });
  } catch (e) {}
  await chrome.storage.local.remove(['cif_session_token', 'cif_token_expires_at', 'cif_user']);
  return { status: 'success' };
}

async function getAuthStatus() {
  const token = await getSessionToken();
  if (!token) {
    return { signedIn: false, user: null };
  }
  const data = await chrome.storage.local.get(['cif_user']);
  if (data.cif_user) {
    return { signedIn: true, user: data.cif_user };
  }
  const meRes = await apiRequest('api/me');
  if (meRes && meRes.status === 'success') {
    await chrome.storage.local.set({ cif_user: meRes });
    return { signedIn: true, user: meRes };
  }
  return { signedIn: false, user: null };
}

// --- Message Router with Sender Verification (Step 8.7) ---

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Security rule 1: sender must be our own extension context
  if (sender.id !== chrome.runtime.id) {
    sendResponse({ status: 'error', message: 'Unauthorized message sender' });
    return false;
  }

  const check = validateMessage(message);
  if (!check.valid) {
    sendResponse({ status: 'error', message: check.error });
    return false;
  }

  const handleAsync = async () => {
    switch (message.type) {
      case MessageTypes.GET_AUTH_STATUS:
        return await getAuthStatus();

      case MessageTypes.SIGN_IN:
        return await signIn();

      case MessageTypes.SIGN_OUT:
        return await signOut();

      case MessageTypes.GET_REPO_STATUS: {
        const repo = message.repo;
        if (!repo) return { status: 'error', message: 'Missing repo parameter' };
        return await apiRequest(`api/repos/status?repo=${encodeURIComponent(repo)}`);
      }

      case MessageTypes.ADD_REPO: {
        const repo = message.repo;
        if (!repo) return { status: 'error', message: 'Missing repo parameter' };
        return await apiRequest('api/repos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo })
        });
      }

      case MessageTypes.GET_PR_ANALYSIS: {
        const { repo, number, head_sha } = message;
        if (!repo || !number) return { status: 'error', message: 'Missing repo or number' };
        let path = `api/pr-analysis?repo=${encodeURIComponent(repo)}&number=${encodeURIComponent(number)}`;
        if (head_sha) path += `&head_sha=${encodeURIComponent(head_sha)}`;
        return await apiRequest(path);
      }

      case MessageTypes.GET_FILE_CONTEXT: {
        const { repo, path, ref, line } = message;
        if (!repo || !path) return { status: 'error', message: 'Missing repo or path' };
        let q = `api/file-context?repo=${encodeURIComponent(repo)}&path=${encodeURIComponent(path)}`;
        if (ref) q += `&ref=${encodeURIComponent(ref)}`;
        if (line) q += `&line=${encodeURIComponent(line)}`;
        return await apiRequest(q);
      }

      case MessageTypes.SEND_FEEDBACK: {
        const { finding_id, action, decision_id, pr_id, reason } = message;
        return await apiRequest('api/findings/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ finding_id, action, decision_id, pr_id, reason })
        });
      }

      case MessageTypes.GET_CONFIG: {
        const url = await getBackendBaseUrl();
        return { status: 'success', backend_url: url };
      }

      case MessageTypes.SET_CONFIG: {
        const url = message.backend_url;
        await chrome.storage.local.set({ cif_backend_url: url });
        return { status: 'success', backend_url: url };
      }

      default:
        return { status: 'error', message: `Unhandled message: ${message.type}` };
    }
  };

  handleAsync().then(sendResponse).catch((err) => {
    sendResponse({ status: 'error', message: err.message });
  });

  return true; // Keep channel open for async response
});

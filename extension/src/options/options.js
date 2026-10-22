/**
 * CIF Chrome Extension - Options Page Controller (Step 8.7)
 * Strictly zero innerHTML. Validates allowed origin list before updating storage.
 */

import { MessageTypes } from '../lib/messages.js';
import { ALLOWED_ORIGINS } from '../lib/api.js';

async function init() {
  const select = document.getElementById('backend-url-select');
  const btnSave = document.getElementById('btn-save');
  const statusMsg = document.getElementById('status-msg');

  const res = await chrome.runtime.sendMessage({ type: MessageTypes.GET_CONFIG });
  const current = (res && res.backend_url) ? res.backend_url : 'http://127.0.0.1:8080';

  if (select) {
    select.value = current;
  }

  if (btnSave) {
    btnSave.addEventListener('click', async () => {
      const selected = select.value;
      if (!ALLOWED_ORIGINS.includes(selected)) {
        statusMsg.textContent = 'Selected URL is not in the security allowlist.';
        statusMsg.style.color = '#ef4444';
        return;
      }

      await chrome.runtime.sendMessage({
        type: MessageTypes.SET_CONFIG,
        backend_url: selected
      });

      statusMsg.textContent = 'Settings saved successfully.';
      statusMsg.style.color = '#10b981';
      setTimeout(() => {
        statusMsg.textContent = '';
      }, 2500);
    });
  }
}

window.addEventListener('DOMContentLoaded', init);

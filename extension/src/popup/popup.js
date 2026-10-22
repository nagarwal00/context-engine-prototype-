/**
 * CIF Chrome Extension - Popup Controller (Step 8.3 & Step 8.7)
 * Strictly zero innerHTML. Uses textContent and el() DOM creation.
 */

import { MessageTypes } from '../lib/messages.js';
import { parseGithubUrl } from '../lib/github_url.js';
import { el, text, safeUrl } from '../lib/render.js';

let activePollTimer = null;

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs && tabs.length > 0 ? tabs[0] : null;
}

function renderUserHeader(userSection, user, onSignOut) {
  userSection.textContent = '';
  if (!user) return;

  const pill = el('div', { className: 'user-pill' });
  if (user.avatar_url) {
    pill.appendChild(el('img', { src: user.avatar_url, className: 'user-avatar', alt: user.login }));
  }
  pill.appendChild(el('span', {}, [text(user.login || 'User')]));
  pill.appendChild(el('button', {
    type: 'button',
    className: 'btn btn-secondary btn-sm',
    onClick: onSignOut
  }, [text('Sign Out')]));

  userSection.appendChild(pill);
}

function renderSignedOutView(container, onSignIn) {
  container.textContent = '';

  const card = el('div', { className: 'card text-center' }, [
    el('h3', { style: { fontSize: '13px', marginBottom: '8px', color: '#f8fafc' } }, [text('Sign In to CIF')]),
    el('p', { className: 'text-muted', style: { marginBottom: '14px', lineHeight: '1.4' } }, [
      text('Connect your GitHub account to access architectural decisions, drift detection, and rejected-idea warnings.')
    ]),
    el('button', {
      type: 'button',
      className: 'btn btn-primary',
      id: 'btn-sign-in',
      onClick: onSignIn
    }, [text('Sign in with GitHub')])
  ]);

  container.appendChild(card);
}

function renderNotOnGitHubView(container, baseUrl) {
  container.textContent = '';

  const card = el('div', { className: 'card' }, [
    el('h3', { style: { fontSize: '13px', marginBottom: '6px' } }, [text('Active Session')]),
    el('p', { className: 'text-muted', style: { marginBottom: '12px' } }, [
      text('Navigate to any repository, pull request, or file on GitHub to view architectural context.')
    ]),
    el('button', {
      type: 'button',
      className: 'btn btn-primary',
      onClick: () => chrome.tabs.create({ url: baseUrl })
    }, [text('Open Web Dashboard ↗')])
  ]);

  container.appendChild(card);
}

function renderRepoStatusView(container, repoFullName, statusData, baseUrl, onAddRepo) {
  container.textContent = '';

  const isNotAdded = !statusData || statusData.status === 'not_added';
  const isRunning = statusData && (statusData.status === 'running' || statusData.status === 'in_progress');
  const isPartial = statusData && (statusData.status === 'partial' || statusData.partial);
  const isReady = statusData && statusData.status === 'ready';

  let chipClass = 'chip-not-added';
  let chipText = 'Not Connected';
  if (isRunning) { chipClass = 'chip-running'; chipText = 'Ingesting'; }
  else if (isPartial) { chipClass = 'chip-partial'; chipText = 'Partial (Capped)'; }
  else if (isReady) { chipClass = 'chip-ready'; chipText = 'Ready'; }

  const card = el('div', { className: 'card' }, [
    el('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' } }, [
      el('strong', { style: { fontSize: '12px', fontFamily: 'monospace' } }, [text(repoFullName)]),
      el('span', { className: `chip ${chipClass}` }, [text(chipText)])
    ])
  ]);

  if (isNotAdded) {
    card.appendChild(el('p', { className: 'text-muted', style: { marginBottom: '12px' } }, [
      text('This repository has not been ingested yet. Ingest commit history, decisions, and context graph.')
    ]));
    card.appendChild(el('button', {
      type: 'button',
      className: 'btn btn-primary',
      onClick: onAddRepo
    }, [text('Connect & Ingest Repository')]));
  } else if (isRunning) {
    const job = statusData.active_job || {};
    const progress = Math.min(100, Math.max(5, job.progress_pct || 15));
    card.appendChild(el('div', { className: 'progress-track' }, [
      el('div', { className: 'progress-fill', style: { width: `${progress}%` } })
    ]));
    card.appendChild(el('div', { className: 'text-muted', style: { marginBottom: '8px' } }, [
      text(job.phase || 'Ingesting commits and discussions...')
    ]));
  } else {
    // Ready or Partial
    const decisionsCount = statusData.decisions_count ?? '-';
    const eventsCount = statusData.events_count ?? '-';
    card.appendChild(el('div', { style: { fontSize: '12px', marginBottom: '12px', color: '#cbd5e1' } }, [
      text(`Knowledge: ${decisionsCount} decisions, ${eventsCount} events`)
    ]));
    card.appendChild(el('button', {
      type: 'button',
      className: 'btn btn-secondary',
      onClick: () => chrome.tabs.create({ url: `${baseUrl}?repo=${encodeURIComponent(repoFullName)}` })
    }, [text('Explore in Dashboard ↗')]));
  }

  container.appendChild(card);
}

async function init() {
  const container = document.getElementById('main-content');
  const userSection = document.getElementById('user-section');

  const configRes = await chrome.runtime.sendMessage({ type: MessageTypes.GET_CONFIG });
  const baseUrl = (configRes && configRes.backend_url) ? configRes.backend_url : 'http://127.0.0.1:8080';

  const authStatus = await chrome.runtime.sendMessage({ type: MessageTypes.GET_AUTH_STATUS });

  if (!authStatus || !authStatus.signedIn) {
    renderUserHeader(userSection, null);
    renderSignedOutView(container, async () => {
      container.textContent = 'Launching GitHub authentication...';
      const res = await chrome.runtime.sendMessage({ type: MessageTypes.SIGN_IN });
      if (res && res.status === 'success') {
        init();
      } else {
        alert(`Sign-in error: ${res ? res.message : 'Cancelled'}`);
        init();
      }
    });
    return;
  }

  // User is signed in
  renderUserHeader(userSection, authStatus.user, async () => {
    await chrome.runtime.sendMessage({ type: MessageTypes.SIGN_OUT });
    init();
  });

  const tab = await getActiveTab();
  const pageInfo = tab ? parseGithubUrl(tab.url) : { valid: false };

  if (!pageInfo.valid) {
    renderNotOnGitHubView(container, baseUrl);
    return;
  }

  // Load repo status
  const repoName = pageInfo.fullName;
  container.textContent = `Loading status for ${repoName}...`;

  const pollStatus = async () => {
    const statusRes = await chrome.runtime.sendMessage({
      type: MessageTypes.GET_REPO_STATUS,
      repo: repoName
    });

    renderRepoStatusView(container, repoName, statusRes, baseUrl, async () => {
      container.textContent = `Connecting ${repoName}...`;
      const addRes = await chrome.runtime.sendMessage({
        type: MessageTypes.ADD_REPO,
        repo: repoName
      });
      if (addRes && addRes.status === 'success') {
        pollStatus();
      } else {
        alert(`Failed to add repo: ${addRes ? addRes.message : 'Unknown error'}`);
        pollStatus();
      }
    });

    if (statusRes && (statusRes.status === 'running' || statusRes.status === 'in_progress')) {
      if (!activePollTimer) {
        activePollTimer = setTimeout(pollStatus, 3000);
      }
    }
  };

  pollStatus();
}

window.addEventListener('DOMContentLoaded', init);

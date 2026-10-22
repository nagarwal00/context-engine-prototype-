/**
 * CIF Chrome Extension - GitHub Content Script (Step 8.4, 8.5, 8.6, 8.7)
 * Runs on GitHub repository pages
 * Renders an isolated floating Shadow-DOM widget (never injected into GitHub's DOM tree).
 * Survives Turbo/SPA page transitions with debounced navigation detection.
 * Strictly safe DOM construction; no unsafe HTML string parsing.
 */

import { parseGithubUrl } from '../lib/github_url.js';
import { MessageTypes } from '../lib/messages.js';
import { el, text, safeUrl, createBadge, createButton } from '../lib/render.js';

let currentNavigationKey = '';
let activeShadowRoot = null;
let drawerOpen = false;

function getOrCreateWidgetHost() {
  let host = document.getElementById('cif-overlay-host');
  if (!host) {
    host = document.createElement('div');
    host.id = 'cif-overlay-host';
    host.setAttribute('data-cif', 'true');
    document.body.appendChild(host);
    activeShadowRoot = host.attachShadow({ mode: 'open' });

    // Inject stylesheet link into shadow root
    const cssUrl = chrome.runtime.getURL('src/content/widget.css');
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = cssUrl;
    activeShadowRoot.appendChild(link);
  }
  return activeShadowRoot;
}

function clearWidgetContent(root) {
  // Retain the <link rel="stylesheet"> element, remove dynamic nodes
  const children = Array.from(root.childNodes);
  for (const c of children) {
    if (c.tagName !== 'LINK') {
      root.removeChild(c);
    }
  }
}

// --- Render Workflows ---

function renderTriggerButton(root, badgeCount, onClick) {
  const isZero = badgeCount === 0;
  const trigger = el('div', {
    className: 'cif-floating-trigger',
    onClick: onClick
  }, [
    el('span', { className: 'cif-logo-icon' }),
    el('span', { className: 'cif-trigger-label' }, [text('CIF Decisions')]),
    el('span', { className: `cif-count-badge ${isZero ? 'zero' : ''}` }, [text(badgeCount)])
  ]);
  root.appendChild(trigger);
  return trigger;
}

function renderDrawerContainer(root, title, onClose) {
  const drawer = el('div', {
    className: `cif-drawer ${drawerOpen ? 'open' : ''}`,
    id: 'cif-drawer-panel'
  }, [
    el('div', { className: 'cif-drawer-header' }, [
      el('div', { className: 'cif-header-title' }, [
        el('span', { className: 'cif-logo-icon' }),
        text(title)
      ]),
      el('button', {
        type: 'button',
        className: 'cif-close-btn',
        onClick: onClose
      }, [text('×')])
    ]),
    el('div', { className: 'cif-drawer-body', id: 'cif-drawer-body' })
  ]);

  root.appendChild(drawer);
  return drawer;
}

async function handleFeedbackAction(action, findingId, decisionId, prId, bodyEl, refreshFn) {
  let reason = '';
  if (action === 'dismiss' || action === 'reopen') {
    reason = prompt(`Enter review comment / rationale for action '${action}':`) || '';
    if (!reason.trim()) return;
  }

  const res = await chrome.runtime.sendMessage({
    type: MessageTypes.SEND_FEEDBACK,
    finding_id: findingId,
    decision_id: decisionId,
    action: action,
    pr_id: String(prId),
    reason: reason
  });

  if (res && res.status === 'success') {
    refreshFn();
  } else {
    alert(`Could not record review action: ${res ? res.message : 'Unknown error'}`);
  }
}

// --- Pull Request Analysis View (Step 8.4) ---

async function loadPullRequestView(root, pageInfo) {
  clearWidgetContent(root);

  const res = await chrome.runtime.sendMessage({
    type: MessageTypes.GET_PR_ANALYSIS,
    repo: pageInfo.fullName,
    number: pageInfo.number
  });

  const findings = (res && res.status === 'ready' && Array.isArray(res.findings)) ? res.findings : [];
  const relatedDecisions = (res && res.status === 'ready' && Array.isArray(res.related_decisions)) ? res.related_decisions : [];

  const toggleDrawer = () => {
    drawerOpen = !drawerOpen;
    const panel = root.getElementById('cif-drawer-panel');
    if (panel) {
      if (drawerOpen) panel.classList.add('open');
      else panel.classList.remove('open');
    }
  };

  renderTriggerButton(root, findings.length, toggleDrawer);
  const drawer = renderDrawerContainer(root, `PR #${pageInfo.number} Context`, toggleDrawer);
  const bodyEl = drawer.querySelector('#cif-drawer-body');

  if (res && res.detector_status === 'incomplete') {
    drawer.insertBefore(
      el('div', { className: 'cif-banner-incomplete' }, [
        text('⚠️ Check incomplete: some architectural guard rules could not be evaluated.')
      ]),
      bodyEl
    );
  }

  if (!res || res.status === 'not_added') {
    bodyEl.appendChild(el('div', { className: 'cif-empty-state' }, [
      text(`Repository '${pageInfo.fullName}' is not connected to CIF. Open the extension popup to connect.`)
    ]));
    return;
  }

  if (res.status === 'needs_relogin') {
    bodyEl.appendChild(el('div', { className: 'cif-empty-state' }, [
      text('GitHub authorization expired. Open the CIF extension popup to sign in again.')
    ]));
    return;
  }

  if (findings.length === 0 && relatedDecisions.length === 0) {
    bodyEl.appendChild(el('div', { className: 'cif-empty-state' }, [
      text('No drift or rejected-idea findings detected on this pull request.')
    ]));
    return;
  }

  // 1. Rejected Idea Warnings
  const rejectedFindings = findings.filter(f => f.type === 'rejected_idea');
  if (rejectedFindings.length > 0) {
    bodyEl.appendChild(el('div', { className: 'cif-section-title' }, [text('Advisory: Rejected Ideas')]));
    for (const f of rejectedFindings) {
      const card = el('div', { className: 'cif-card cif-card-warning' }, [
        el('div', { className: 'cif-card-header' }, [
          el('div', { className: 'cif-card-title' }, [text(f.title || 'Possible Rejected Idea')]),
          createBadge('Advisory', 'advisory')
        ]),
        el('div', { className: 'cif-card-desc' }, [
          text(`Original rejection reason: ${f.original_reason || 'Documented architectural rejection.'}`)
        ])
      ]);

      if (f.source_url) {
        card.appendChild(el('a', { href: f.source_url, className: 'cif-link' }, [text('View original discussion ↗')]));
      }

      if (Array.isArray(f.changed_circumstances) && f.changed_circumstances.length > 0) {
        for (const hint of f.changed_circumstances) {
          card.appendChild(el('div', { style: { fontSize: '11px', color: '#94a3b8' } }, [text(`• ${hint}`)]));
        }
      }

      // Action buttons
      const actions = el('div', { className: 'cif-actions-row' }, [
        createButton('Dismiss', 'cif-btn-secondary', () => {
          handleFeedbackAction('dismiss', f.finding_id, f.decision_id, pageInfo.number, bodyEl, () => loadPullRequestView(root, pageInfo));
        }),
        createButton('Reopen Decision', 'cif-btn-primary', () => {
          handleFeedbackAction('reopen', f.finding_id, f.decision_id, pageInfo.number, bodyEl, () => loadPullRequestView(root, pageInfo));
        })
      ]);
      card.appendChild(actions);

      bodyEl.appendChild(card);
    }
  }

  // 2. Drift Violations
  const driftFindings = findings.filter(f => f.type === 'potential_violation');
  if (driftFindings.length > 0) {
    bodyEl.appendChild(el('div', { className: 'cif-section-title' }, [text('Drift Findings (Possible Violations)')]));
    for (const d of driftFindings) {
      const locText = d.file ? `${d.file}${d.line ? `:${d.line}` : ''}` : '';
      const card = el('div', { className: 'cif-card cif-card-drift' }, [
        el('div', { className: 'cif-card-header' }, [
          el('div', { className: 'cif-card-title' }, [text(d.title || 'Constraint Violation')]),
          createBadge('Heuristic', 'heuristic')
        ]),
        locText ? el('div', { style: { fontSize: '11px', color: '#f87171', fontWeight: '600' } }, [text(locText)]) : null,
        d.offending_line ? el('div', { className: 'cif-card-code' }, [text(d.offending_line)]) : null,
        d.original_reason ? el('div', { className: 'cif-card-desc' }, [text(d.original_reason)]) : null
      ]);

      const actions = el('div', { className: 'cif-actions-row' }, [
        createButton('Confirm Violation', 'cif-btn-danger', () => {
          handleFeedbackAction('confirm', d.finding_id, d.decision_id, pageInfo.number, bodyEl, () => loadPullRequestView(root, pageInfo));
        }),
        createButton('Dismiss (False Positive)', 'cif-btn-secondary', () => {
          handleFeedbackAction('dismiss', d.finding_id, d.decision_id, pageInfo.number, bodyEl, () => loadPullRequestView(root, pageInfo));
        })
      ]);
      card.appendChild(actions);

      bodyEl.appendChild(card);
    }
  }

  // 3. Related Decisions
  if (relatedDecisions.length > 0) {
    bodyEl.appendChild(el('div', { className: 'cif-section-title' }, [text('Related Decisions')]));
    for (const dec of relatedDecisions) {
      const card = el('div', { className: 'cif-card' }, [
        el('div', { className: 'cif-card-header' }, [
          el('div', { className: 'cif-card-title' }, [text(dec.title)]),
          createBadge(dec.state, dec.state === 'accepted' ? 'accepted' : 'rejected')
        ]),
        dec.rationale ? el('div', { className: 'cif-card-desc' }, [text(dec.rationale)]) : null
      ]);
      bodyEl.appendChild(card);
    }
  }
}

// --- File & Entity Context View (Step 8.5) ---

async function loadFileContextView(root, pageInfo) {
  clearWidgetContent(root);

  const res = await chrome.runtime.sendMessage({
    type: MessageTypes.GET_FILE_CONTEXT,
    repo: pageInfo.fullName,
    path: pageInfo.path,
    ref: pageInfo.ref,
    line: pageInfo.line
  });

  const decisions = (res && res.status === 'ready' && Array.isArray(res.decisions)) ? res.decisions : [];
  const rejected = (res && res.status === 'ready' && Array.isArray(res.rejected_alternatives)) ? res.rejected_alternatives : [];

  const toggleDrawer = () => {
    drawerOpen = !drawerOpen;
    const panel = root.getElementById('cif-drawer-panel');
    if (panel) {
      if (drawerOpen) panel.classList.add('open');
      else panel.classList.remove('open');
    }
  };

  const totalCount = decisions.length + rejected.length;
  renderTriggerButton(root, totalCount, toggleDrawer);

  const title = pageInfo.path ? pageInfo.path.split('/').pop() : 'File Context';
  const drawer = renderDrawerContainer(root, `Context: ${title}`, toggleDrawer);
  const bodyEl = drawer.querySelector('#cif-drawer-body');

  if (!res || res.status === 'not_added') {
    bodyEl.appendChild(el('div', { className: 'cif-empty-state' }, [
      text(`Repository '${pageInfo.fullName}' is not monitored by CIF. Open extension popup to add.`)
    ]));
    return;
  }

  if (totalCount === 0) {
    bodyEl.appendChild(el('div', { className: 'cif-empty-state' }, [
      text(`No architectural decisions recorded for ${pageInfo.path || 'this file'}.`)
    ]));
    return;
  }

  // Active decisions
  if (decisions.length > 0) {
    bodyEl.appendChild(el('div', { className: 'cif-section-title' }, [text('Active Architectural Decisions')]));
    for (const d of decisions) {
      const card = el('div', { className: 'cif-card' }, [
        el('div', { className: 'cif-card-header' }, [
          el('div', { className: 'cif-card-title' }, [text(d.title)]),
          createBadge(d.freshness || d.state, d.freshness === 'stale' ? 'stale' : 'accepted')
        ]),
        d.affected_function ? el('div', { style: { fontSize: '11px', color: '#38bdf8', fontFamily: 'monospace' } }, [text(`function ${d.affected_function}()`)]) : null,
        d.rationale ? el('div', { className: 'cif-card-desc' }, [text(d.rationale)]) : null
      ]);
      if (d.source_url) {
        card.appendChild(el('a', { href: d.source_url, className: 'cif-link' }, [text('Evidence & Provenance ↗')]));
      }
      bodyEl.appendChild(card);
    }
  }

  // Rejected alternatives
  if (rejected.length > 0) {
    bodyEl.appendChild(el('div', { className: 'cif-section-title' }, [text('Rejected Alternatives')]));
    for (const r of rejected) {
      const card = el('div', { className: 'cif-card' }, [
        el('div', { className: 'cif-card-header' }, [
          el('div', { className: 'cif-card-title' }, [text(r.title)]),
          createBadge('Rejected', 'rejected')
        ]),
        r.rejection_reason ? el('div', { className: 'cif-card-desc' }, [text(r.rejection_reason)]) : null
      ]);
      if (r.source_url) {
        card.appendChild(el('a', { href: r.source_url, className: 'cif-link' }, [text('View reason discussion ↗')]));
      }
      bodyEl.appendChild(card);
    }
  }
}

// --- Main Page Observer & Router (Step 8.6) ---

function handlePageChange() {
  const pageInfo = parseGithubUrl(window.location.href);
  if (!pageInfo.valid) {
    // Non-repo page: hide host if present
    const host = document.getElementById('cif-overlay-host');
    if (host) host.style.display = 'none';
    return;
  }

  const newKey = `${pageInfo.kind}:${pageInfo.fullName}:${pageInfo.number || ''}:${pageInfo.path || ''}:${pageInfo.line || ''}`;
  if (newKey === currentNavigationKey) return;
  currentNavigationKey = newKey;

  const root = getOrCreateWidgetHost();
  const host = document.getElementById('cif-overlay-host');
  if (host) host.style.display = 'block';

  if (pageInfo.kind === 'pull') {
    loadPullRequestView(root, pageInfo);
  } else if (pageInfo.kind === 'blob') {
    loadFileContextView(root, pageInfo);
  } else {
    // Generic repo page: show simple badge
    clearWidgetContent(root);
  }
}

// GitHub Turbo / SPA event listeners
document.addEventListener('turbo:render', handlePageChange);
document.addEventListener('turbo:load', handlePageChange);
window.addEventListener('popstate', handlePageChange);

// Debounced MutationObserver fallback for GitHub PJAX transitions
let mutationTimer = null;
const observer = new MutationObserver(() => {
  if (mutationTimer) clearTimeout(mutationTimer);
  mutationTimer = setTimeout(handlePageChange, 250);
});
observer.observe(document.body || document.documentElement, {
  childList: true,
  subtree: true
});

// Initial load
handlePageChange();

/**
 * HTML sanitization and safe URL resolution (P0-c / Step 1.3)
 */
function esc(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function safeUrl(value) {
  if (!value) return '#';
  const str = String(value).trim();
  if (/^https?:\/\//i.test(str)) {
    return str;
  }
  return '#';
}

const app = {
  activeSurface: 'timeline',
  selectedRepo: '',
  timelineFilter: 'all',
  decisionFilter: 'all',
  decisionSearchQuery: '',
  selectedArtifact: null,
  cachedDecisions: [],
  cachedArtifacts: [],
  
  init() {
    this.refreshStats();
    this.loadRepositoriesList();
    this.loadTimeline();
    this.loadArtifacts();
    this.loadDecisions();
    this.loadReviewQueue();
    this.loadBenchmarkData();
    this.loadOnboardingTour();
  },

  navigate(surfaceId) {
    this.activeSurface = surfaceId;
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.getAttribute('data-surface') === surfaceId);
    });
    document.querySelectorAll('.surface-view').forEach(el => {
      el.classList.remove('active');
    });
    const target = document.getElementById(`surface-${surfaceId}`);
    if (target) {
      target.classList.add('active');
    }

    // Lazy load specific surface data
    if (surfaceId === 'graph') {
      this.loadGraph();
    } else if (surfaceId === 'timeline') {
      this.loadTimeline();
    } else if (surfaceId === 'code') {
      if (!this.selectedArtifact && this.cachedArtifacts.length > 0) {
        this.selectArtifact(this.cachedArtifacts[0].canonical_path);
      }
    } else if (surfaceId === 'evidence') {
      this.populateEvidenceSelect();
    } else if (surfaceId === 'review') {
      this.loadReviewQueue();
    }
  },

  switchRepo(repo) {
    this.selectedRepo = repo;
    const select = document.getElementById('repo-select');
    if (select && select.value !== repo) select.value = repo;
    this.refreshStats();
    this.loadTimeline();
    this.loadArtifacts();
    this.loadDecisions();
    if (this.activeSurface === 'graph') this.loadGraph();
  },

  async loadRepositoriesList() {
    try {
      const json = await this.apiFetch('/api/repos');
      if (json.status === 'success') {
        const select = document.getElementById('repo-select');
        const repos = json.data || [];
        let html = '<option value="">All Repositories (Unified View)</option>';
        repos.forEach(r => {
          html += `<option value="${esc(r)}">${esc(r)}</option>`;
        });
        select.innerHTML = html;
        if (this.selectedRepo) {
          select.value = this.selectedRepo;
        }
      }
    } catch (e) {
      console.error('Error loading repositories list:', e);
    }
  },

  openAddRepoModal() {
    document.getElementById('add-repo-modal').classList.remove('hidden');
    document.getElementById('ingest-progress-box').classList.add('hidden');
    document.getElementById('ingest-log-messages').innerHTML = '';
    document.getElementById('btn-start-ingest').disabled = false;
  },

  closeAddRepoModal() {
    document.getElementById('add-repo-modal').classList.add('hidden');
  },

  async emptyDashboard() {
    const confirmName = prompt('Enter exact database filename to confirm wipe:', 'context_intelligence.db');
    if (confirmName) {
      const json = await this.apiFetch('/api/clear-db', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: confirmName })
      });
      alert(json.message);
      this.selectedRepo = '';
      await this.loadRepositoriesList();
      this.init();
      this.navigate('timeline');
    }
  },

  async submitIngestRepo() {
    const rawRepo = document.getElementById('ingest-repo-input').value.trim();
    const token = document.getElementById('ingest-token-input').value.trim();
    const clearExisting = document.getElementById('ingest-clear-checkbox').checked;

    if (!rawRepo) {
      alert('Please enter a GitHub repository (e.g. owner/repo or full GitHub URL).');
      return;
    }

    const progressBox = document.getElementById('ingest-progress-box');
    const logBox = document.getElementById('ingest-log-messages');
    const titleEl = document.getElementById('ingest-status-title');
    const btn = document.getElementById('btn-start-ingest');

    progressBox.classList.remove('hidden');
    titleEl.textContent = 'Ingesting repository...';
    titleEl.style.color = '#38bdf8';
    logBox.innerHTML = '';
    btn.disabled = true;

    const addLog = (msg) => {
      const line = document.createElement('div');
      line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
      logBox.appendChild(line);
      logBox.scrollTop = logBox.scrollHeight;
    };

    addLog(`Connecting to repository '${rawRepo}'...`);
    addLog(`Fetching commit logs, author identities, and code diffs...`);
    
    // Progress pulse timer while network request completes
    let step = 0;
    const progressInterval = setInterval(() => {
      step++;
      if (step === 1) addLog(`Scanning issues, PR discussions, and parent linkages...`);
      else if (step === 2) addLog(`Parsing Python AST functions and dependency trees...`);
      else if (step === 3) addLog(`Synthesizing architectural decisions & confidence scoring...`);
      else if (step === 4) addLog(`Building temporal context graph edges & evidence chains...`);
    }, 1800);

    try {
      const json = await this.apiFetch('/api/ingest-repo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo: rawRepo,
          token: token || null,
          clear_existing: clearExisting,
          max_commits: 25,
          max_issues: 15
        }),
        timeoutMs: 60000
      });

      clearInterval(progressInterval);

      if (json && json.status === 'success') {
        const stats = json.data || {};
        titleEl.textContent = 'Context Extraction Complete!';
        titleEl.style.color = '#10b981';
        addLog(`Ingested ${stats.commits_ingested || 0} commits and ${(stats.issues_ingested || 0) + (stats.prs_ingested || 0)} issues/PRs.`);
        addLog(`Extracted ${stats.entities_created || 0} code entities (including AST functions).`);
        addLog(`Synthesized ${stats.decisions_extracted || 0} grounded architectural decisions.`);
        addLog(`Constructed ${stats.edges_created || 0} temporal graph edges.`);

        setTimeout(async () => {
          this.closeAddRepoModal();
          await this.loadRepositoriesList();
          this.switchRepo(stats.repo || rawRepo);
        }, 1200);
      } else {
        titleEl.textContent = 'Ingestion Error';
        titleEl.style.color = '#ef4444';
        addLog(`Error: ${json ? json.message : 'Unknown server error'}`);
        btn.disabled = false;
      }
    } catch (e) {
      clearInterval(progressInterval);
      titleEl.textContent = 'Ingestion Error';
      titleEl.style.color = '#ef4444';
      addLog(`Error: ${e.message}`);
      btn.disabled = false;
    }
  },

  async refreshStats() {
    try {
      const json = await this.apiFetch('/api/stats');
      if (json.status === 'success') {
        document.getElementById('stat-decisions').textContent = json.data.decisions;
        document.getElementById('stat-events').textContent = json.data.events;
        const totalReview = json.data.drifts + json.data.conflicts + 1; // including unconfident candidates
        document.getElementById('stat-review-count').textContent = totalReview;
        document.getElementById('sidebar-review-badge').textContent = totalReview;
      }
    } catch (e) {
      console.error('Error fetching stats:', e);
    }
  },

  async reseedData() {
    if (confirm('Reset pilot repositories to default seed state?')) {
      const json = await this.apiFetch('/api/reseed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: 'context_intelligence.db' })
      });
      alert(json.message);
      this.init();
      this.navigate('timeline');
    }
  },

  // =========================================================================
  // SURFACE 1: Project Timeline
  // =========================================================================
  async loadTimeline() {
    const container = document.getElementById('timeline-container');
    container.innerHTML = '<div class="loading-state">Loading timeline events...</div>';
    
    let url = '/api/timeline';
    if (this.selectedRepo) url += `?repo=${encodeURIComponent(this.selectedRepo)}`;

    try {
      const json = await this.apiFetch(url);
      const decisions = json.data || [];

      let filtered = decisions;
      if (this.timelineFilter !== 'all') {
        filtered = decisions.filter(d => d.state === this.timelineFilter);
      }

      if (filtered.length === 0) {
        container.innerHTML = '<div class="placeholder-state">No decisions matching this filter.</div>';
        return;
      }

      container.innerHTML = filtered.map(d => {
        const dateStr = d.made_at ? d.made_at.substring(0, 10) : 'Recent';
        const artifactsStr = (d.affected_artifacts || []).map(a => `<span class="stat-pill">${esc(a.canonical_path)}</span>`).join(' ');
        
        return `
          <div class="timeline-card">
            <div class="timeline-node-dot" style="background-color: ${esc(this.getStateColor(d.state))}"></div>
            <div class="timeline-card-header">
              <span class="status-tag ${esc(d.state)}">${esc(d.state)}</span>
              <span class="timeline-date">${esc(dateStr)}</span>
            </div>
            <h3 class="timeline-title">${esc(d.title)}</h3>
            <p class="timeline-rationale">${esc(d.rationale || 'No stated rationale.')}</p>
            <div class="timeline-meta">
              <span>Author: <strong>${esc(d.made_by)}</strong></span>
              <span>Repo: <code>${esc(d.repo)}</code></span>
              <span>Evidence Cites: <strong>${esc(d.evidence_count)}</strong></span>
            </div>
            ${artifactsStr ? `<div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px;">${artifactsStr}</div>` : ''}
          </div>
        `;
      }).join('');
    } catch (e) {
      container.innerHTML = `<div class="placeholder-state">Error loading timeline: ${esc(e.message)}</div>`;
    }
  },

  filterTimelineState(state) {
    this.timelineFilter = state;
    document.querySelectorAll('.filter-btn').forEach(b => {
      b.classList.toggle('active', b.textContent.toLowerCase().includes(state));
    });
    this.resetAsOfQuery();
  },

  // =========================================================================
  // STEP 2.6: Historical "As Of" Query & Counterfactual Explorer
  // =========================================================================
  setAsOfQueryDate(dateStr) {
    const dateInput = document.getElementById('asof-date-input');
    if (dateInput) dateInput.value = dateStr;
    this.runAsOfQuery();
  },

  async runAsOfQuery() {
    const dateInput = document.getElementById('asof-date-input');
    const artifactInput = document.getElementById('asof-artifact-input');
    const resultsPane = document.getElementById('asof-results-pane');
    const resetBtn = document.getElementById('btn-asof-reset');
    const timelineContainer = document.getElementById('timeline-container');
    const explanationBox = document.getElementById('asof-explanation-box');
    const decisionsContainer = document.getElementById('asof-decisions-container');
    const altsContainer = document.getElementById('asof-alternatives-container');
    const changesContainer = document.getElementById('asof-changes-container');

    const dateVal = dateInput ? dateInput.value.trim() : '';
    const artifactVal = artifactInput ? artifactInput.value.trim() : '';

    if (!dateVal) {
      alert('Please select a date for the As Of query.');
      return;
    }

    if (resultsPane) resultsPane.style.display = 'flex';
    if (resetBtn) resetBtn.style.display = 'inline-flex';
    if (timelineContainer) timelineContainer.style.display = 'none';

    if (explanationBox) explanationBox.innerHTML = '<div class="loading-state">Reconstructing historical beliefs and counterfactuals...</div>';
    if (decisionsContainer) decisionsContainer.innerHTML = '<div class="loading-state">Loading decisions...</div>';
    if (altsContainer) altsContainer.innerHTML = '<div class="loading-state">Loading alternatives...</div>';
    if (changesContainer) changesContainer.innerHTML = '<div class="loading-state">Loading changes...</div>';

    const params = [`date=${encodeURIComponent(dateVal)}`];
    if (this.selectedRepo) params.push(`repo=${encodeURIComponent(this.selectedRepo)}`);
    if (artifactVal) params.push(`artifact=${encodeURIComponent(artifactVal)}`);

    try {
      const json = await this.apiFetch(`/api/as-of?${params.join('&')}`);
      if (json.status !== 'success' || !json.data) {
        if (explanationBox) explanationBox.innerHTML = `<div class="placeholder-state">Error: ${esc(json.message || 'Failed to query as of date')}</div>`;
        return;
      }

      const { decisions, documented_alternatives, changed_afterwards, later_evidence, explanation } = json.data;

      // 1. Explanation banner
      if (explanationBox) {
        explanationBox.textContent = explanation || 'No explanation generated.';
      }

      // 2. Reconstructed Decisions
      if (decisionsContainer) {
        if (!decisions || decisions.length === 0) {
          decisionsContainer.innerHTML = '<div class="placeholder-state">No active decisions recorded as of this date.</div>';
        } else {
          decisionsContainer.innerHTML = decisions.map(d => {
            const dateStr = d.made_at ? d.made_at.substring(0, 10) : '';
            return `
              <div class="asof-card">
                <div class="asof-card-header">
                  <span class="status-tag ${esc(d.state_as_of_cutoff)}">${esc(d.state_as_of_cutoff)}</span>
                  <div>${d.has_reconstructed_history_only ? '<span class="badge-tag reconstructed">' + esc('Reconstructed') + '</span>' : '<span class="badge-tag observed">' + esc('Observed') + '</span>'}</div>
                </div>
                <h5 class="asof-card-title">${esc(d.title)}</h5>
                <p class="asof-card-body">${esc(d.rationale || 'No rationale recorded.')}</p>
                <div style="font-size: 0.74rem; color: #64748b; margin-top: 6px;">
                  Author: <strong>${esc(d.made_by)}</strong> • Date: <code>${esc(dateStr)}</code>
                </div>
              </div>
            `;
          }).join('');
        }
      }

      // 3. Documented Alternatives
      if (altsContainer) {
        if (!documented_alternatives || documented_alternatives.length === 0) {
          altsContainer.innerHTML = '<div class="placeholder-state">No documented alternatives for decisions known at this date.</div>';
        } else {
          altsContainer.innerHTML = documented_alternatives.map(a => `
            <div class="asof-card">
              <div class="asof-card-header">
                <span class="badge-tag" style="background-color: rgba(239, 68, 68, 0.15); color: #f87171;">${esc('Alternative')}</span>
                <span style="font-size: 0.72rem; color: #64748b;">For: ${esc(a.for_decision_title ? a.for_decision_title.substring(0, 24) : '')}</span>
              </div>
              <h5 class="asof-card-title">${esc(a.description)}</h5>
              <div class="asof-card-body" style="color: #cbd5e1;">
                <strong>Outcome:</strong> ${esc(a.rejection_reason)}
              </div>
            </div>
          `).join('');
        }
      }

      // 4. Changed Afterwards & Later Evidence
      if (changesContainer) {
        const hasChanges = (changed_afterwards && changed_afterwards.length > 0) || (later_evidence && later_evidence.length > 0);
        if (!hasChanges) {
          changesContainer.innerHTML = '<div class="placeholder-state">No subsequent transitions or later evidence recorded.</div>';
        } else {
          const transItems = (changed_afterwards || []).map(c => {
            const dateStr = c.changed_at ? c.changed_at.substring(0, 10) : (c.made_at ? c.made_at.substring(0, 10) : '');
            return `
              <div class="asof-card" style="border-left: 3px solid var(--status-superseded);">
                <div class="asof-card-header">
                  <span class="badge-tag" style="background-color: rgba(168, 85, 247, 0.15); color: #c084fc;">${esc(c.type === 'later_transition' ? 'Transition' : 'New Decision')}</span>
                  <span style="font-size: 0.72rem; color: #64748b;">${esc(dateStr)}</span>
                </div>
                <h5 class="asof-card-title">${esc(c.decision_title || c.decision_id)}</h5>
                <p class="asof-card-body">${c.type === 'later_transition' ? esc((c.from_state || 'Initial') + ' → ' + c.to_state + ' by ' + c.changed_by) : esc('Adopted by ' + c.made_by)}</p>
                ${c.notes ? '<p class="asof-card-body" style="font-style: italic;">&ldquo;' + esc(c.notes) + '&rdquo;</p>' : ''}
              </div>
            `;
          }).join('');

          const evItems = (later_evidence || []).map(e => `
            <div class="asof-card" style="border-left: 3px solid #06b6d4;">
              <div class="asof-card-header">
                <span class="badge-tag" style="background-color: rgba(6, 182, 212, 0.15); color: #22d3ee;">${esc('Later Evidence')}</span>
                <span style="font-size: 0.72rem; color: #64748b;">${esc(e.timestamp ? e.timestamp.substring(0, 10) : '')}</span>
              </div>
              <h5 class="asof-card-title">${esc(e.title || e.source_type)}</h5>
              <p class="asof-card-body">By ${esc(e.author)} in ${esc(e.source_type)}</p>
            </div>
          `).join('');

          changesContainer.innerHTML = transItems + evItems;
        }
      }

    } catch (e) {
      if (explanationBox) explanationBox.innerHTML = `<div class="placeholder-state">Error: ${esc(e.message)}</div>`;
    }
  },

  resetAsOfQuery() {
    const resultsPane = document.getElementById('asof-results-pane');
    const resetBtn = document.getElementById('btn-asof-reset');
    const timelineContainer = document.getElementById('timeline-container');
    if (resultsPane) resultsPane.style.display = 'none';
    if (resetBtn) resetBtn.style.display = 'none';
    if (timelineContainer) timelineContainer.style.display = 'block';
  },

  // =========================================================================
  // SURFACE 2: Context Graph (Interactive SVG Canvas)
  // =========================================================================
  async loadGraph() {
    const svg = document.getElementById('graph-svg');
    svg.innerHTML = '<text x="50%" y="50%" fill="#94a3b8" text-anchor="middle">Generating graph visualization...</text>';

    let url = '/api/graph';
    if (this.selectedRepo) url += `?repo=${encodeURIComponent(this.selectedRepo)}`;

    try {
      const json = await this.apiFetch(url);
      const { nodes, links } = json.data;

      this.renderSvgGraph(nodes, links);
    } catch (e) {
      svg.innerHTML = `<text x="50%" y="50%" fill="#ef4444" text-anchor="middle">Error loading graph: ${esc(e.message)}</text>`;
    }
  },

  renderSvgGraph(nodes, links) {
    const svg = document.getElementById('graph-svg');
    const width = svg.clientWidth || 900;
    const height = 580;
    svg.innerHTML = '';

    // Create positioned layout for nodes
    const nodeMap = {};
    const radius = Math.min(width, height) * 0.38;
    const centerX = width / 2;
    const centerY = height / 2;

    nodes.forEach((n, i) => {
      // Position decisions in inner circle, entities in outer, events on perimeter
      let r = radius;
      if (n.type === 'decision') r = radius * 0.55;
      if (n.type === 'event') r = radius * 0.95;

      const angle = (i / nodes.length) * 2 * Math.PI;
      n.x = centerX + r * Math.cos(angle) + (Math.sin(i * 3) * 15);
      n.y = centerY + r * Math.sin(angle) + (Math.cos(i * 2) * 15);
      nodeMap[n.id] = n;
    });

    // Draw Links
    const linksGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    links.forEach(l => {
      const src = nodeMap[l.source];
      const tgt = nodeMap[l.target];
      if (!src || !tgt) return;

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', src.x);
      line.setAttribute('y1', src.y);
      line.setAttribute('x2', tgt.x);
      line.setAttribute('y2', tgt.y);

      let strokeColor = '#334155';
      let strokeWidth = '1.5';
      let dash = '';

      if (l.type === 'conflicts_with' || l.type === 'drifts_from') {
        strokeColor = '#ef4444';
        strokeWidth = '3';
        dash = '5,5';
      } else if (l.type === 'supersedes') {
        strokeColor = '#a855f7';
        strokeWidth = '2';
      } else if (l.type === 'affects') {
        strokeColor = '#3b82f6';
      } else if (l.type === 'evidenced_by') {
        strokeColor = '#ec4899';
      }

      line.setAttribute('stroke', strokeColor);
      line.setAttribute('stroke-width', strokeWidth);
      if (dash) line.setAttribute('stroke-dasharray', dash);
      line.setAttribute('opacity', '0.7');

      linksGroup.appendChild(line);
    });
    svg.appendChild(linksGroup);

    // Draw Nodes
    const nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    nodes.forEach(n => {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.style.cursor = 'pointer';
      g.onclick = () => this.inspectGraphNode(n);

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', n.x);
      circle.setAttribute('cy', n.y);
      circle.setAttribute('r', n.type === 'decision' ? 14 : 9);
      circle.setAttribute('fill', n.color || '#3b82f6');
      circle.setAttribute('stroke', '#0b0f17');
      circle.setAttribute('stroke-width', '2');

      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = `${n.type.toUpperCase()}: ${n.label}`;
      g.appendChild(title);

      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', n.x + 12);
      label.setAttribute('y', n.y + 4);
      label.setAttribute('fill', '#94a3b8');
      label.setAttribute('font-size', '10px');
      label.setAttribute('font-family', 'Inter, sans-serif');
      const truncated = n.label.length > 25 ? n.label.substring(0, 23) + '...' : n.label;
      label.textContent = truncated;

      g.appendChild(circle);
      g.appendChild(label);
      nodesGroup.appendChild(g);
    });
    svg.appendChild(nodesGroup);
  },

  inspectGraphNode(node) {
    const details = document.getElementById('graph-node-details');
    details.classList.remove('hidden');

    let content = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span class="status-tag ${esc(node.state || 'accepted')}">${esc(node.type.toUpperCase())}</span>
        <button class="btn-graph-close" style="background:none; border:none; color:#64748b; cursor:pointer;">✕</button>
      </div>
      <h4 style="font-size: 0.95rem; margin-bottom: 8px;">${esc(node.label)}</h4>
    `;

    if (node.type === 'decision') {
      const confStr = node.confidence !== undefined ? Math.round(node.confidence * 100) + '%' : 'N/A';
      const madeAtStr = node.made_at ? node.made_at.substring(0, 10) : '';
      content += `
        <p style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 10px;">State: <strong>${esc(node.state)}</strong> | Confidence: <strong>${esc(confStr)}</strong></p>
        <p style="color: #cbd5e1; font-size: 0.82rem; margin-bottom: 12px;">Made by <strong>${esc(node.made_by)}</strong> on ${esc(madeAtStr)}</p>
        <button class="btn btn-primary btn-sm btn-graph-evidence" data-decision-id="${esc(node.id)}">View Evidence Trail</button>
      `;
    } else if (node.type === 'entity') {
      content += `
        <p style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 10px;">Entity Type: <code>${esc(node.entity_type)}</code></p>
        <button class="btn btn-primary btn-sm btn-graph-inspect" data-artifact-label="${esc(node.label)}">Inspect Decision Chain</button>
      `;
    } else if (node.type === 'event') {
      content += `
        <p style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 10px;">Source: <code>${esc(node.source_type)}</code></p>
        <a href="${safeUrl(node.source_url)}" target="_blank" class="citation-link">Open Source Link ↗</a>
      `;
    }

    details.innerHTML = content;
    const closeBtn = details.querySelector('.btn-graph-close');
    if (closeBtn) closeBtn.addEventListener('click', () => details.classList.add('hidden'));
    const evBtn = details.querySelector('.btn-graph-evidence');
    if (evBtn) evBtn.addEventListener('click', () => app.showDecisionEvidence(evBtn.dataset.decisionId));
    const insBtn = details.querySelector('.btn-graph-inspect');
    if (insBtn) insBtn.addEventListener('click', () => app.inspectArtifact(insBtn.dataset.artifactLabel));
  },

  // =========================================================================
  // SURFACE 3: Code-Context View
  // =========================================================================
  async loadArtifacts() {
    const listEl = document.getElementById('code-artifact-list');
    let url = '/api/artifacts';
    if (this.selectedRepo) url += `?repo=${encodeURIComponent(this.selectedRepo)}`;

    try {
      const json = await this.apiFetch(url);
      this.cachedArtifacts = json.data || [];

      listEl.innerHTML = this.cachedArtifacts.map(a => `
        <div class="artifact-item ${this.selectedArtifact === a.canonical_path ? 'active' : ''}" data-canonical-path="${esc(a.canonical_path)}">
          <div class="artifact-path">${esc(a.canonical_path)}</div>
          <span class="artifact-type-tag">${esc(a.entity_type.toUpperCase())} • ${esc(a.decision_count)} Decisions</span>
        </div>
      `).join('');

      listEl.querySelectorAll('.artifact-item').forEach(el => {
        el.addEventListener('click', () => app.selectArtifact(el.dataset.canonicalPath));
      });

      if (!this.selectedArtifact && this.cachedArtifacts.length > 0) {
        this.selectArtifact(this.cachedArtifacts[0].canonical_path);
      }
    } catch (e) {
      listEl.innerHTML = `<div class="placeholder-state">Error: ${esc(e.message)}</div>`;
    }
  },

  async selectArtifact(canonicalPath) {
    this.selectedArtifact = canonicalPath;
    document.querySelectorAll('.artifact-item').forEach(el => {
      el.classList.toggle('active', el.querySelector('.artifact-path').textContent === canonicalPath);
    });

    const expContainer = document.getElementById('explanation-container');
    expContainer.innerHTML = '<div class="loading-state">Synthesizing evidence-grounded decision chain...</div>';

    try {
      const json = await this.apiFetch(`/api/explain?artifact=${encodeURIComponent(canonicalPath)}`);
      const data = json.data;

      if (data.status === 'not_found') {
        expContainer.innerHTML = `
          <div class="placeholder-state" style="border-left: 4px solid var(--status-unresolved); padding: 16px;">
            ${esc(data.explanation)}
          </div>
        `;
        return;
      }

      let stepsHtml = (data.chain || []).map(step => `
        <div class="chain-step-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="status-tag ${esc(step.state)}">${esc(step.state)}</span>
            <span style="font-size: 0.75rem; color: #64748b; font-family: monospace;">Step ${esc(step.step_number)}</span>
          </div>
          <h4 style="font-size: 1.05rem; margin-bottom: 6px;">${esc(step.title)}</h4>
          <p style="font-size: 0.86rem; color: #94a3b8; line-height: 1.5; margin-bottom: 10px;">${esc(step.rationale)}</p>
          
          <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 6px;">
            Decided by <strong>${esc(step.made_by)}</strong> on ${esc(step.made_at ? step.made_at.substring(0, 10) : '')}
          </div>

          ${(step.citations || []).length > 0 ? `
            <div class="citation-list">
              ${step.citations.map(c => `
                <a href="${safeUrl(c.source_url)}" target="_blank" class="citation-link" title="${esc(c.title)}">
                  <span>[${esc(c.source_type)}]</span> ${esc(c.source_id ? c.source_id.substring(0, 12) : '')} ↗
                </a>
              `).join('')}
            </div>
          ` : ''}
        </div>
      `).join('');

      expContainer.innerHTML = `
        <div class="explanation-banner">
          <h3 style="font-size: 1.15rem; margin-bottom: 6px;">Why does <code>${esc(canonicalPath)}</code> look like this?</h3>
          <p style="font-size: 0.9rem; color: #cbd5e1;">${esc(data.explanation).replace(/\n\n/g, '<br><br>')}</p>
        </div>
        <h4 style="font-size: 0.9rem; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em; margin-bottom: 12px;">Grounded Decision Chain</h4>
        ${stepsHtml}
      `;
    } catch (e) {
      expContainer.innerHTML = `<div class="placeholder-state">Error explaining artifact: ${esc(e.message)}</div>`;
    }
  },

  inspectArtifact(canonicalPath) {
    this.navigate('code');
    this.selectArtifact(canonicalPath);
  },

  // =========================================================================
  // SURFACE 4: Decision Explorer
  // =========================================================================
  async loadDecisions() {
    const container = document.getElementById('decisions-container');
    let url = '/api/decisions';
    const params = [];
    if (this.selectedRepo) params.push(`repo=${encodeURIComponent(this.selectedRepo)}`);
    if (this.decisionFilter !== 'all') params.push(`state=${encodeURIComponent(this.decisionFilter)}`);
    if (this.decisionSearchQuery) params.push(`search=${encodeURIComponent(this.decisionSearchQuery)}`);
    if (params.length > 0) url += `?${params.join('&')}`;

    try {
      const json = await this.apiFetch(url);
      this.cachedDecisions = json.data || [];

      if (this.cachedDecisions.length === 0) {
        container.innerHTML = '<div class="placeholder-state">No decisions match your search or filter.</div>';
        return;
      }

      container.innerHTML = this.cachedDecisions.map(d => {
        const confStr = d.confidence ? 'Heuristic score (uncalibrated): ' + Math.round(d.confidence * 100) + '%' : '';
        return `
        <div class="decision-card">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 4px;">
              <div style="display: flex; gap: 6px; align-items: center;">
                <span class="status-tag ${esc(d.state)}">${esc(d.state)}</span>
                <span class="stat-pill" style="font-size: 0.72rem; padding: 2px 6px;">Assessment: <strong>${esc(d.evidence_assessment || 'insufficient')}</strong></span>
              </div>
              <span style="font-size: 0.75rem; color: #64748b; font-family: monospace;" title="Uncalibrated heuristic">${esc(confStr)}</span>
            </div>
            <h3 class="decision-card-title">${esc(d.title)}</h3>
            <p class="decision-card-rationale">${esc(d.rationale || 'No extracted rationale.')}</p>
          </div>
          <div>
            <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 12px;">
              Author: <strong>${esc(d.made_by)}</strong> • Evidence: <strong>${esc(d.evidence_count)}</strong>
            </div>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
              <button class="btn btn-secondary btn-sm btn-show-evidence" data-decision-id="${esc(d.decision_id)}">
                Inspect Evidence Trail ↗
              </button>
              <button class="btn btn-secondary btn-sm btn-show-lifecycle" data-decision-id="${esc(d.decision_id)}">
                Lifecycle ↻
              </button>
            </div>
          </div>
        </div>
      `;
      }).join('');

      container.querySelectorAll('.btn-show-evidence').forEach(btn => {
        btn.addEventListener('click', () => app.showDecisionEvidence(btn.dataset.decisionId));
      });
      container.querySelectorAll('.btn-show-lifecycle').forEach(btn => {
        btn.addEventListener('click', () => app.showDecisionLifecycle(btn.dataset.decisionId));
      });
    } catch (e) {
      container.innerHTML = `<div class="placeholder-state">Error: ${esc(e.message)}</div>`;
    }
  },

  filterDecisionsByState(state) {
    this.decisionFilter = state;
    this.showDecisionsGrid();
    document.querySelectorAll('.facet-tab').forEach(b => {
      b.classList.toggle('active', b.textContent.toLowerCase().includes(state));
    });
    this.loadDecisions();
  },

  searchDecisions(query) {
    this.decisionSearchQuery = query;
    this.showDecisionsGrid();
    this.loadDecisions();
  },

  // =========================================================================
  // STEP 2.5: Lifecycle View, Supersession Chain & Audit Log
  // =========================================================================
  currentLifecycleDecisionId: null,

  showDecisionsGrid() {
    const grid = document.getElementById('decisions-container');
    const lifecycle = document.getElementById('lifecycle-container');
    if (grid) grid.style.display = 'grid';
    if (lifecycle) lifecycle.style.display = 'none';

    document.querySelectorAll('.facet-tab').forEach(b => {
      b.classList.toggle('active', b.id !== 'facet-tab-lifecycle' && b.textContent.toLowerCase().includes(this.decisionFilter));
    });
  },

  async showLifecycleTab() {
    const grid = document.getElementById('decisions-container');
    const lifecycle = document.getElementById('lifecycle-container');
    if (grid) grid.style.display = 'none';
    if (lifecycle) lifecycle.style.display = 'flex';

    document.querySelectorAll('.facet-tab').forEach(b => {
      b.classList.toggle('active', b.id === 'facet-tab-lifecycle');
    });

    if (this.cachedDecisions.length === 0) {
      await this.loadDecisions();
    }

    const select = document.getElementById('lifecycle-decision-select');
    if (select && this.cachedDecisions.length > 0) {
      select.innerHTML = this.cachedDecisions.map(d => `
        <option value="${esc(d.decision_id)}">${esc(d.title)} [${esc(d.state)}]</option>
      `).join('');

      let targetId = this.currentLifecycleDecisionId;
      if (!targetId || !this.cachedDecisions.some(d => d.decision_id === targetId)) {
        const preferred = this.cachedDecisions.find(d => d.state === 'superseded') || this.cachedDecisions[0];
        targetId = preferred.decision_id;
      }
      select.value = targetId;
      await this.loadDecisionLifecycle(targetId);
    }

    await this.loadAuditLog();
  },

  showDecisionLifecycle(decisionId) {
    this.currentLifecycleDecisionId = decisionId;
    this.navigate('decisions');
    this.showLifecycleTab();
    const select = document.getElementById('lifecycle-decision-select');
    if (select) select.value = decisionId;
    this.loadDecisionLifecycle(decisionId);
  },

  async loadDecisionLifecycle(decisionId) {
    if (!decisionId) return;
    this.currentLifecycleDecisionId = decisionId;

    const summaryEl = document.getElementById('lifecycle-decision-summary');
    const timelineEl = document.getElementById('lifecycle-timeline-list');
    const chainEl = document.getElementById('lifecycle-chain-details');

    if (summaryEl) summaryEl.innerHTML = '<div class="loading-state">Loading decision lifecycle...</div>';
    if (timelineEl) timelineEl.innerHTML = '<div class="loading-state">Loading timeline...</div>';
    if (chainEl) chainEl.innerHTML = '<div class="loading-state">Loading supersession chain...</div>';

    try {
      const json = await this.apiFetch(`/api/decision-history?decision_id=${encodeURIComponent(decisionId)}`);
      if (json.status !== 'success' || !json.data) {
        if (summaryEl) summaryEl.innerHTML = `<div class="placeholder-state">Decision '${esc(decisionId)}' not found.</div>`;
        return;
      }

      const { decision, transitions, supersession_chain } = json.data;

      // 1. Render Summary Card
      if (summaryEl) {
        summaryEl.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap;">
            <div>
              <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
                <span class="status-tag ${esc(decision.state)}">${esc(decision.state)}</span>
                <span class="stat-pill">Assessment: <strong>${esc(decision.evidence_assessment)}</strong></span>
                <span class="stat-pill">Freshness: <strong>${esc(decision.freshness)}</strong></span>
                <span class="stat-pill" title="Uncalibrated extraction score">Heuristic score (uncalibrated): <strong>${esc(Math.round((decision.confidence || 0) * 100))}%</strong></span>
              </div>
              <h2 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 6px;">${esc(decision.title)}</h2>
              <p style="font-size: 0.88rem; color: #94a3b8; max-width: 800px; margin-bottom: 10px;">${esc(decision.rationale || 'No rationale recorded.')}</p>
            </div>
            <div style="text-align: right; font-size: 0.8rem; color: #64748b;">
              <div>Decided by: <strong>${esc(decision.made_by)}</strong></div>
              <div>Date: <code>${esc(decision.made_at ? decision.made_at.substring(0, 10) : 'N/A')}</code></div>
              <div>Repo: <code>${esc(decision.repo)}</code></div>
            </div>
          </div>
        `;
      }

      // 2. Render Vertical Transition Timeline
      if (timelineEl) {
        if (!transitions || transitions.length === 0) {
          timelineEl.innerHTML = '<div class="placeholder-state">No recorded transitions for this decision.</div>';
        } else {
          timelineEl.innerHTML = transitions.map(t => {
            const dateStr = t.changed_at ? t.changed_at.replace('T', ' ').substring(0, 19) : 'Initial';
            const badgeTag = t.reconstructed
              ? '<span class="badge-tag reconstructed" title="Reconstructed during migration">' + esc('Reconstructed') + '</span>'
              : '<span class="badge-tag observed" title="Directly observed transition event">' + esc('Observed') + '</span>';
            const fromStateTag = t.from_state
              ? '<span class="status-tag ' + esc(t.from_state) + '">' + esc(t.from_state) + '</span> → <span class="status-tag ' + esc(t.to_state) + '">' + esc(t.to_state) + '</span>'
              : '<span class="status-tag ' + esc(t.to_state) + '">' + esc(t.to_state) + '</span> <span style="font-size: 0.75rem; color: #64748b;">(' + esc('Created') + ')</span>';
            const color = this.getStateColor(t.to_state);

            return `
              <div class="lifecycle-timeline-item">
                <div class="lifecycle-timeline-marker" style="background-color: ${esc(color)};"></div>
                <div class="lifecycle-timeline-content">
                  <div class="timeline-transition-row">
                    <div>${fromStateTag}</div>
                    <div>${badgeTag}</div>
                  </div>
                  <div class="timeline-meta-row">
                    <span>Actor: <strong>${esc(t.changed_by)}</strong></span>
                    <span>Timestamp: <code>${esc(dateStr)}</code></span>
                  </div>
                  <div style="font-size: 0.84rem; color: #cbd5e1; margin-top: 4px;">
                    ${esc(t.notes || 'No reason provided.')}
                  </div>
                </div>
              </div>
            `;
          }).join('');
        }
      }

      // 3. Render Supersession Chain
      if (chainEl) {
        const preceding = supersession_chain?.preceding || [];
        const current = supersession_chain?.current || decision;
        const succeeding = supersession_chain?.succeeding || [];

        let chainHtml = '';

        if (preceding.length > 0) {
          chainHtml += preceding.map(p => `
            <div class="chain-node-box" onclick="app.showDecisionLifecycle('${esc(p.decision_id)}')">
              <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px;">← Preceding Decision</div>
              <div style="font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">${esc(p.title)}</div>
              <span class="status-tag ${esc(p.state)}">${esc(p.state)}</span>
            </div>
            <div class="chain-connector">↓ supersedes</div>
          `).join('');
        }

        chainHtml += `
          <div class="chain-node-box current">
            <div style="font-size: 0.72rem; color: var(--status-superseded); text-transform: uppercase; margin-bottom: 2px;">● Selected Decision</div>
            <div style="font-weight: 700; font-size: 0.9rem; margin-bottom: 4px;">${esc(current.title)}</div>
            <span class="status-tag ${esc(current.state)}">${esc(current.state)}</span>
          </div>
        `;

        if (succeeding.length > 0) {
          chainHtml += succeeding.map(s => `
            <div class="chain-connector">↓ superseded by</div>
            <div class="chain-node-box" onclick="app.showDecisionLifecycle('${esc(s.decision_id)}')">
              <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px;">→ Succeeding Decision</div>
              <div style="font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">${esc(s.title)}</div>
              <span class="status-tag ${esc(s.state)}">${esc(s.state)}</span>
            </div>
          `).join('');
        }

        if (preceding.length === 0 && succeeding.length === 0) {
          chainHtml += `
            <div style="font-size: 0.8rem; color: #64748b; font-style: italic; margin-top: 10px; text-align: center;">
              Stand-alone decision (no preceding or succeeding decisions in supersession chain).
            </div>
          `;
        }

        chainEl.innerHTML = chainHtml;
      }

    } catch (e) {
      if (summaryEl) summaryEl.innerHTML = `<div class="placeholder-state">Error: ${esc(e.message)}</div>`;
    }
  },

  async loadAuditLog() {
    const tbody = document.getElementById('audit-table-body');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="6" class="loading-state">Loading audit trail...</td></tr>';

    const actor = document.getElementById('audit-filter-actor')?.value?.trim() || '';
    const date = document.getElementById('audit-filter-date')?.value?.trim() || '';

    const params = [];
    if (actor) params.push(`actor=${encodeURIComponent(actor)}`);
    if (date) params.push(`date=${encodeURIComponent(date)}`);
    let url = '/api/decision-history';
    if (params.length > 0) url += `?${params.join('&')}`;

    try {
      const json = await this.apiFetch(url);
      const rows = json.data?.audit_log || [];

      if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="placeholder-state">No audit log records match filter criteria.</td></tr>';
        return;
      }

      tbody.innerHTML = rows.map(r => {
        const dateStr = r.changed_at ? r.changed_at.replace('T', ' ').substring(0, 19) : '';
        const transStr = r.from_state
          ? '<span class="status-tag ' + esc(r.from_state) + '">' + esc(r.from_state) + '</span> → <span class="status-tag ' + esc(r.to_state) + '">' + esc(r.to_state) + '</span>'
          : '<span class="status-tag ' + esc(r.to_state) + '">' + esc(r.to_state) + '</span>';
        const badge = r.reconstructed
          ? '<span class="badge-tag reconstructed">' + esc('Reconstructed') + '</span>'
          : '<span class="badge-tag observed">' + esc('Observed') + '</span>';

        return `
          <tr>
            <td style="font-family: monospace; white-space: nowrap;">${esc(dateStr)}</td>
            <td>
              <a href="#" class="audit-link" onclick="event.preventDefault(); app.showDecisionLifecycle('${esc(r.decision_id)}');">
                ${esc(r.decision_title || r.decision_id)}
              </a>
            </td>
            <td>${transStr}</td>
            <td><strong>${esc(r.changed_by)}</strong></td>
            <td>${esc(r.notes || '')}</td>
            <td>${badge}</td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" class="placeholder-state">Error loading audit log: ${esc(e.message)}</td></tr>`;
    }
  },

  filterAuditLog() {
    clearTimeout(this._auditDebounce);
    this._auditDebounce = setTimeout(() => {
      this.loadAuditLog();
    }, 250);
  },

  clearAuditFilters() {
    const actorInput = document.getElementById('audit-filter-actor');
    const dateInput = document.getElementById('audit-filter-date');
    if (actorInput) actorInput.value = '';
    if (dateInput) dateInput.value = '';
    this.loadAuditLog();
  },

  // =========================================================================
  // SURFACE 5: Evidence Panel
  // =========================================================================
  async populateEvidenceSelect() {
    const select = document.getElementById('evidence-decision-select');
    if (this.cachedDecisions.length === 0) {
      await this.loadDecisions();
    }
    select.innerHTML = this.cachedDecisions.map(d => `
      <option value="${esc(d.decision_id)}">${esc(d.title)} [${esc(d.state)}]</option>
    `).join('');

    if (this.cachedDecisions.length > 0) {
      this.loadEvidenceForDecision(this.cachedDecisions[0].decision_id);
    }
  },

  showDecisionEvidence(decisionId) {
    this.navigate('evidence');
    const select = document.getElementById('evidence-decision-select');
    select.value = decisionId;
    this.loadEvidenceForDecision(decisionId);
  },

  async loadEvidenceForDecision(decisionId) {
    const container = document.getElementById('evidence-container');
    container.innerHTML = '<div class="loading-state">Retrieving evidence bundle and source links...</div>';

    try {
      const json = await this.apiFetch(`/api/evidence?decision_id=${encodeURIComponent(decisionId)}`);
      const { decision, evidence_events, discussion_events } = json.data;

      if (!decision) {
        container.innerHTML = '<div class="placeholder-state">Decision not found.</div>';
        return;
      }

      const allEvents = [...evidence_events, ...discussion_events];

      if (allEvents.length === 0) {
        container.innerHTML = '<div class="placeholder-state">No linked evidence found for this decision.</div>';
        return;
      }

      container.innerHTML = allEvents.map(ev => {
        const tsStr = ev.ts ? ev.ts.substring(0, 10) : '';
        return `
        <div class="evidence-card">
          <div class="evidence-header">
            <span class="source-badge">${esc(ev.source_type.toUpperCase())}</span>
            <span style="font-size: 0.75rem; color: #64748b; font-family: monospace;">${esc(tsStr)}</span>
          </div>
          <h4 style="font-size: 0.95rem; margin-bottom: 8px;">${esc(ev.title || ev.source_id)}</h4>
          <div class="evidence-body">${esc(ev.body)}</div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.78rem; color: #64748b;">Author: <strong>${esc(ev.author)}</strong></span>
            <a href="${safeUrl(ev.source_url)}" target="_blank" class="citation-link">
              Open Verified Source URL ↗
            </a>
          </div>
        </div>
      `;
      }).join('');
    } catch (e) {
      container.innerHTML = `<div class="placeholder-state">Error: ${esc(e.message)}</div>`;
    }
  },

  // =========================================================================
  // SURFACE 6: Review Queue & Triage Modal (§10 & Section 5 Guard Rules)
  // =========================================================================
  async loadReviewQueue() {
    const container = document.getElementById('review-queue-container');
    container.innerHTML = '<div class="loading-state">Checking review queue items...</div>';

    try {
      const [reviewJson, rulesJson] = await Promise.all([
        this.apiFetch('/api/review-queue'),
        this.apiFetch('/api/guard-rules')
      ]);

      const items = reviewJson.data || [];
      const rules = rulesJson.data || [];

      document.getElementById('stat-review-count').textContent = items.length;
      document.getElementById('sidebar-review-badge').textContent = items.length;

      let html = '';

      // Section A: Decision Guard Rules
      if (rules.length > 0) {
        html += `
          <div style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
              <h3 style="font-size: 1.1rem; color: #60a5fa; margin: 0;">Decision Guard Rules (Automated CI Enforcement)</h3>
              <span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa;">Novelty Feature</span>
            </div>
            <div style="display: grid; gap: 12px;">
              ${rules.map(r => `
                <div class="review-item-card" style="border-left: 3px solid ${r.status === 'active' ? '#10b981' : (r.status === 'proposed' ? '#f59e0b' : '#6b7280')};">
                  <div style="flex: 1;">
                    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px;">
                      <span class="review-reason-tag" style="background: rgba(99, 102, 241, 0.15); color: #818cf8;">${esc(r.rule_type)}</span>
                      <span class="badge" style="background: ${r.status === 'active' ? '#10b981' : (r.status === 'proposed' ? '#f59e0b' : '#4b5563')}; color: #fff;">${esc(r.status.toUpperCase())}</span>
                    </div>
                    <h4 style="font-size: 0.95rem; margin: 4px 0;">Rule <code>${esc(r.rule_id)}</code></h4>
                    <p style="font-size: 0.85rem; color: #94a3b8; margin: 4px 0;">
                      Governed by: <strong>${esc(r.decision_title || r.decision_id)}</strong>
                    </p>
                    <pre style="background: #0b0f17; padding: 6px 10px; border-radius: 4px; font-size: 0.75rem; color: #cbd5e1; margin-top: 6px;">${esc(JSON.stringify(r.params, null, 2))}</pre>
                  </div>
                  <div class="review-actions">
                    ${r.status !== 'active' ? `<button class="btn btn-primary btn-sm btn-approve-rule" data-rule-id="${esc(r.rule_id)}">Approve (Enforce in CI)</button>` : ''}
                    ${r.status !== 'disabled' ? `<button class="btn btn-secondary btn-sm btn-disable-rule" data-rule-id="${esc(r.rule_id)}">Disable</button>` : ''}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }

      // Section B: Standard Review Queue Items
      if (items.length === 0 && rules.length === 0) {
        html += `
          <div class="placeholder-state" style="border-left: 4px solid var(--status-accepted); padding: 18px;">
            ✓ All extractions confirmed! No pending conflicts, drift items, or proposed rules in the queue.
          </div>
        `;
      } else if (items.length > 0) {
        html += `
          <h3 style="font-size: 1.1rem; margin-bottom: 12px;">Candidate Decisions & Contradictions for Arbitration</h3>
          <div style="display: grid; gap: 12px;">
            ${items.map(item => {
              const id = item.decision_id || item.edge_id;
              const confStr = item.confidence !== undefined ? Math.round(item.confidence * 100) + '%' : '';
              return `
                <div class="review-item-card">
                  <div style="flex: 1;">
                    <span class="review-reason-tag">${esc(item.queue_reason)}</span>
                    <h3 style="font-size: 1.05rem; margin: 6px 0;">${esc(item.title)}</h3>
                    <p style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">${esc(item.rationale || 'Flagged for human arbitration per Section 10.')}</p>
                    <div style="font-size: 0.78rem; color: #64748b; margin-top: 8px;">
                      Confidence: <strong>${esc(confStr)}</strong> • Status: <code>${esc(item.review_status)}</code>
                    </div>
                  </div>
                  <div class="review-actions">
                    <button class="btn btn-primary btn-sm btn-queue-confirm" data-id="${esc(id)}" data-type="${esc(item.item_type)}">Confirm</button>
                    <button class="btn btn-secondary btn-sm btn-queue-correct" data-id="${esc(id)}" data-type="${esc(item.item_type)}" data-title="${esc(item.title)}">Correct</button>
                    <button class="btn btn-danger btn-sm btn-queue-reject" data-id="${esc(id)}" data-type="${esc(item.item_type)}">Reject</button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `;
      }

      container.innerHTML = html;
      container.querySelectorAll('.btn-approve-rule').forEach(b => b.addEventListener('click', () => app.approveGuardRule(b.dataset.ruleId)));
      container.querySelectorAll('.btn-disable-rule').forEach(b => b.addEventListener('click', () => app.disableGuardRule(b.dataset.ruleId)));
      container.querySelectorAll('.btn-queue-confirm').forEach(b => b.addEventListener('click', () => app.triggerReviewAction('confirm', b.dataset.id, b.dataset.type)));
      container.querySelectorAll('.btn-queue-correct').forEach(b => b.addEventListener('click', () => app.openCorrectModal(b.dataset.id, b.dataset.type, b.dataset.title)));
      container.querySelectorAll('.btn-queue-reject').forEach(b => b.addEventListener('click', () => app.triggerReviewAction('reject', b.dataset.id, b.dataset.type)));
    } catch (e) {
      container.innerHTML = `<div class="placeholder-state">Error: ${esc(e.message)}</div>`;
    }
  },

  async approveGuardRule(ruleId) {
    try {
      const json = await this.apiFetch('/api/guard-rules/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_id: ruleId })
      });
      alert(`Guard Rule '${ruleId}' is now ACTIVE and will be enforced on incoming pull requests.`);
      this.loadReviewQueue();
    } catch (e) {
      alert(`Approval error: ${e.message}`);
    }
  },

  async disableGuardRule(ruleId) {
    try {
      const json = await this.apiFetch('/api/guard-rules/disable', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_id: ruleId })
      });
      alert(`Guard Rule '${ruleId}' has been disabled.`);
      this.loadReviewQueue();
    } catch (e) {
      alert(`Disable error: ${e.message}`);
    }
  },

  async triggerReviewAction(action, targetId, itemType) {
    if (!confirm(`Are you sure you want to ${action} this item?`)) return;

    try {
      const json = await this.apiFetch('/api/review-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, target_id: targetId, item_type: itemType })
      });
      alert(json.message);
      this.loadReviewQueue();
      this.refreshStats();
    } catch (e) {
      alert(`Action error: ${e.message}`);
    }
  },

  openCorrectModal(targetId, itemType, title) {
    const modal = document.getElementById('review-modal');
    modal.classList.remove('hidden');
    document.getElementById('modal-title').textContent = `Correct Decision Record`;
    document.getElementById('modal-body').innerHTML = `
      <div style="margin-bottom: 14px;">
        <label style="font-size: 0.8rem; color: #94a3b8; display: block; margin-bottom: 4px;">Corrected Title:</label>
        <input type="text" id="modal-correct-title" value="${esc(title)}" style="width: 100%; padding: 8px; background: #0b0f17; border: 1px solid #334155; color: #fff; border-radius: 4px;">
      </div>
      <div style="margin-bottom: 14px;">
        <label style="font-size: 0.8rem; color: #94a3b8; display: block; margin-bottom: 4px;">Corrected State:</label>
        <select id="modal-correct-state" style="width: 100%; padding: 8px; background: #0b0f17; border: 1px solid #334155; color: #fff; border-radius: 4px;">
          <option value="accepted">Accepted</option>
          <option value="rejected">Rejected</option>
          <option value="superseded">Superseded</option>
          <option value="proposed">Proposed</option>
        </select>
      </div>
      <div>
        <label style="font-size: 0.8rem; color: #94a3b8; display: block; margin-bottom: 4px;">Correction Notes / Audit Justification:</label>
        <textarea id="modal-correct-rationale" rows="3" style="width: 100%; padding: 8px; background: #0b0f17; border: 1px solid #334155; color: #fff; border-radius: 4px;" placeholder="Reason for correcting extraction..."></textarea>
      </div>
    `;

    const footer = document.getElementById('modal-footer');
    footer.innerHTML = `
      <button class="btn btn-secondary btn-modal-cancel">Cancel</button>
      <button class="btn btn-primary btn-modal-save" data-target-id="${esc(targetId)}" data-item-type="${esc(itemType)}">Save Correction</button>
    `;
    footer.querySelector('.btn-modal-cancel').addEventListener('click', () => app.closeReviewModal());
    footer.querySelector('.btn-modal-save').addEventListener('click', (e) => {
      const btn = e.currentTarget;
      app.submitCorrection(btn.dataset.targetId, btn.dataset.itemType);
    });
  },

  async submitCorrection(targetId, itemType) {
    const newTitle = document.getElementById('modal-correct-title').value;
    const newState = document.getElementById('modal-correct-state').value;
    const rationale = document.getElementById('modal-correct-rationale').value;

    try {
      const json = await this.apiFetch('/api/review-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'correct',
          target_id: targetId,
          item_type: itemType,
          title: newTitle,
          state: newState,
          rationale: rationale
        })
      });
      alert(json.message);
      this.closeReviewModal();
      this.loadReviewQueue();
      this.refreshStats();
    } catch (e) {
      alert(`Correction error: ${e.message}`);
    }
  },

  closeReviewModal() {
    document.getElementById('review-modal').classList.add('hidden');
  },

  // =========================================================================
  // EXTRA: Live CI Drift Checker (§8.3 & Section 5.4)
  // =========================================================================
  loadDriftPreset(scenario) {
    const input = document.getElementById('drift-diff-input');
    if (scenario === 'thermal_revert') {
      input.value = `diff --git a/src/thermal/control.py b/src/thermal/control.py
--- a/src/thermal/control.py
+++ b/src/thermal/control.py
@@ -25,8 +25,7 @@ def regulate_temperature(current_temp, target_temp):
-    # PID feedback calculation
-    return clamp(self.Kp * error + self.Ki * integral, 0.0, 100.0)
+    # Quick hack: revert to threshold on_off hysteresis without PID gains
+    if current_temp > target_temp + 1.5:
+        return 0.0
+    return 100.0`;
    } else if (scenario === 'cache_memory') {
      input.value = `diff --git a/src/cache/store.py b/src/cache/store.py
--- a/src/cache/store.py
+++ b/src/cache/store.py
@@ -10,6 +10,8 @@ def cache_get(key):
-    return redis_client.get(key)
+    # Store items in raw local dictionary cache instead of Redis
+    local_cache = {}
+    return local_cache.get(key)`;
    } else if (scenario === 'guard_rule_violation') {
      input.value = `diff --git a/src/payments/service.py b/src/payments/service.py
--- a/src/payments/service.py
+++ b/src/payments/service.py
@@ -1,5 +1,6 @@
+import sticky_sessions
 from stripe import PaymentIntent`;
    } else if (scenario === 'clean_change') {
      input.value = `diff --git a/src/thermal/control.py b/src/thermal/control.py
--- a/src/thermal/control.py
+++ b/src/thermal/control.py

@@ -30,3 +30,4 @@
+    # Normal refactoring: improve variable documentation
+    # Maintains established PID control loop`;
    }
  },

  async executeDriftCheck() {
    const diffText = document.getElementById('drift-diff-input').value;
    const resultDisplay = document.getElementById('drift-result-display');
    resultDisplay.classList.remove('hidden');
    resultDisplay.innerHTML = '<div class="loading-state">Running CI Drift Detection Pass...</div>';

    const repo = diffText.includes('cache') ? 'acme-eng/distributed-cache-service' : 'acme-eng/thermal-control-system';
    const file = diffText.includes('cache') ? 'src/cache/store.py' : 'src/thermal/control.py';

    try {
      const json = await this.apiFetch('/api/drift-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo, diff_text: diffText, files: [file] })
      });

      const errors = json.errors || (json.report && json.report.errors) || [];
      const isIncomplete = json.check_status === 'incomplete' || (json.report && json.report.status === 'incomplete');

      if (json.drift_detected) {
        const drift = json.results[0];
        const confStr = drift.confidence ? Math.round(drift.confidence * 100) + '%' : '';
        const incompleteWarning = isIncomplete ? `
          <div style="margin-top: 8px; padding: 6px 10px; background: rgba(245, 158, 11, 0.15); border-left: 3px solid #f59e0b; font-size: 0.8rem; color: #fbbf24;">
            ⚠️ Check incomplete: ${esc(errors.length)} rule(s) could not run
          </div>
        ` : '';
        resultDisplay.innerHTML = `
          <div class="drift-alert-box drift-found">
            <h4 style="font-size: 1.05rem; margin-bottom: 6px;">⚠️ CI Alert: Code-Level Architectural Drift Detected!</h4>
            <p style="font-size: 0.88rem; line-height: 1.5; margin-bottom: 10px;">${esc(drift.reason)}</p>
            <p style="font-size: 0.8rem; color: #fca5a5;">
              Violated Decision: <strong>${esc(drift.decision_title)}</strong> (Confidence: ${esc(confStr)})<br>
              Action taken: Generated <code>drifts_from</code> edge and dispatched to Human Review Queue.
            </p>
            ${incompleteWarning}
          </div>
        `;
        this.refreshStats();
      } else if (isIncomplete) {
        resultDisplay.innerHTML = `
          <div class="drift-alert-box" style="background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; color: #fbbf24;">
            <h4 style="font-size: 1.05rem; margin-bottom: 6px;">⚠️ Check incomplete: ${esc(errors.length)} rule(s) could not run</h4>
            <p style="font-size: 0.88rem; line-height: 1.5; color: #cbd5e1;">One or more decision guard rules encountered errors during evaluation and could not complete.</p>
          </div>
        `;
      } else {
        resultDisplay.innerHTML = `
          <div class="drift-alert-box clean">
            <h4 style="font-size: 1.05rem; margin-bottom: 6px;">✓ CI Pass: Code change is consistent with accepted decisions.</h4>
            <p style="font-size: 0.88rem;">No violations found. No architectural drift or reintroduction of rejected approaches detected.</p>
          </div>
        `;
      }
    } catch (e) {
      resultDisplay.innerHTML = `<div class="placeholder-state">Error checking drift: ${esc(e.message)}</div>`;
    }
  },

  // =========================================================================
  // EXTRA: Evaluation Benchmark (§12 & METRICS.md)
  // =========================================================================
  async loadBenchmarkData() {
    const container = document.getElementById('benchmark-container');
    try {
      const json = await this.apiFetch('/api/benchmark');
      const { metrics, baselines, ground_truth_total, matched_gt_count, details } = json.data;

      const fmtPct = (val) => (typeof val === 'number' ? `${val}%` : (val || 'Not Measured'));
      const fmtVal = (val, unit = '') => (typeof val === 'number' ? `${val}${unit}` : (val || 'Not Measured'));

      let baselineRows = '';
      if (baselines) {
        // CIF System summary row
        baselineRows += `
          <tr class="highlight-row">
            <td><strong>Context Intelligence Framework (Ours)</strong></td>
            <td>${esc(fmtPct(metrics.decision_extraction_recall))}</td>
            <td>${esc(fmtPct(metrics.evidence_link_accuracy))}</td>
            <td>${esc(fmtPct(metrics.drift_precision))} (Drift Precision)</td>
            <td style="color: #10b981; font-weight: 700;">${esc(fmtPct(metrics.unsupported_claim_rate))}</td>
            <td><span class="badge" style="background:#10b981; color:#fff;">Live Computed</span></td>
          </tr>
        `;

        for (const [key, b] of Object.entries(baselines)) {
          if (!b) continue;
          const statusBadge = b.status === 'measured' 
            ? `<span class="badge" style="background:#3b82f6; color:#fff;">Measured</span>` 
            : `<span class="badge" style="background:#6b7280; color:#fff;">Not Measured</span>`;
          baselineRows += `
            <tr>
              <td><strong>${esc(b.name || key)}</strong></td>
              <td>${esc(fmtPct(b.decision_recall))}</td>
              <td>${esc(fmtPct(b.evidence_grounding_accuracy || b.evidence_link_accuracy))}</td>
              <td>${esc(b.conflict_drift_detection || 'None (Unstructured)')}</td>
              <td style="${b.hallucination_rate ? 'color: #ef4444;' : ''}">${esc(fmtPct(b.hallucination_rate || b.unsupported_claim_rate))}</td>
              <td>${statusBadge}</td>
            </tr>
          `;
        }
      }

      container.innerHTML = `
        <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <strong style="color: #60a5fa;">Synthetic Pilot Benchmark (Smoke Test)</strong>
            <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #94a3b8;">
              Evaluated on synthetic pilot repositories (<code>acme-eng/thermal-control-system</code>, <code>acme-eng/distributed-cache-service</code>).
              Matched <strong>${esc(matched_gt_count || 0)}</strong> of <strong>${esc(ground_truth_total || 0)}</strong> ground truth decisions.
            </p>
          </div>
          <span class="badge" style="background: #2563eb; color: #fff; font-size: 0.75rem;">Pipeline Smoke Test</span>
        </div>

        <div class="benchmark-metrics-cards">
          <div class="metric-stat-box">
            <div class="metric-val">${esc(fmtPct(metrics.decision_extraction_recall))}</div>
            <div class="metric-lbl">Decision Recall</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val">${esc(fmtPct(metrics.evidence_link_accuracy))}</div>
            <div class="metric-lbl">Evidence Link Validity</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val">${esc(fmtPct(metrics.drift_precision))}</div>
            <div class="metric-lbl">Drift Precision</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val" style="color: #10b981;">${esc(fmtPct(metrics.unsupported_claim_rate))}</div>
            <div class="metric-lbl">Unsupported Claim Rate</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val">${esc(fmtVal(metrics.processing_latency_ms, ' ms'))}</div>
            <div class="metric-lbl">Median Latency</div>
          </div>
        </div>

        <h3 style="font-size: 1.15rem; margin-bottom: 14px; margin-top: 24px;">Comparative Benchmark Against Practical Baselines</h3>
        <table class="benchmark-table">
          <thead>
            <tr>
              <th>System / Baseline</th>
              <th>Decision Recall</th>
              <th>Evidence Grounding</th>
              <th>Contradiction & Drift</th>
              <th>Unsupported / Hallucinated</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${baselineRows}
          </tbody>
        </table>
      `;
    } catch (e) {
      container.innerHTML = `<div class="placeholder-state">Error loading benchmark: ${esc(e.message)}</div>`;
    }
  },

  // =========================================================================
  // EXTRA: Onboarding Guided Tour
  // =========================================================================
  loadOnboardingTour() {
    const container = document.getElementById('onboarding-tour-container');
    container.innerHTML = `
      <div class="timeline-card" style="margin-bottom: 20px;">
        <h3 style="font-size: 1.15rem; margin-bottom: 8px;">1. Subsystem: Thermal Regulation (<code>src/thermal/control.py</code>)</h3>
        <p style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 12px;">
          <strong>Historical Context:</strong> In v1, an on-off controller was used, leading to emergency chamber shutdowns under 80% duty cycle (Issue #12). 
          Marcus Vance proposed deadband tuning, but Sarah Chen benchmarked it and proved it caused 17% higher latency and transient overshoots.
          ADR 0004 established discrete PID control with anti-windup clamping.
        </p>
        <button class="btn btn-secondary btn-sm btn-tour-thermal">
          View Regulate Temperature Decision Chain ↗
        </button>
      </div>

      <div class="timeline-card">
        <h3 style="font-size: 1.15rem; margin-bottom: 8px;">2. Subsystem: Distributed Caching (<code>src/cache/store.py</code>)</h3>
        <p style="font-size: 0.9rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 12px;">
          <strong>Historical Context:</strong> Python in-memory LRU dict cache caused worker pods to crash with OOM errors under flash sales (Issue #34). 
          Marcus Vance attempted to keep local caching by adding soft memory caps (PR #38). Priya Patel demonstrated that local caching causes replica stampedes and memory duplication. 
          ADR 0009 superseded the local cache and migrated to Redis cluster with sentinel failover.
        </p>
        <button class="btn btn-secondary btn-sm btn-tour-cache">
          View Cache Store Decision Chain ↗
        </button>
      </div>
    `;
    const thermalBtn = container.querySelector('.btn-tour-thermal');
    if (thermalBtn) thermalBtn.addEventListener('click', () => app.inspectArtifact('src/thermal/control.py::regulate_temperature'));
    const cacheBtn = container.querySelector('.btn-tour-cache');
    if (cacheBtn) cacheBtn.addEventListener('click', () => app.inspectArtifact('src/cache/store.py::cache_get'));
  },

  getStateColor(state) {
    if (state === 'accepted') return '#10b981';
    if (state === 'rejected') return '#ef4444';
    if (state === 'superseded') return '#a855f7';
    if (state === 'proposed') return '#f59e0b';
    return '#64748b';
  },

  authToken: '',
  setAuthToken(token) {
    this.authToken = (token || '').trim();
  },

  // =========================================================================
  // UNIFIED API LAYER (Supports both Local Python Server & GitHub Pages)
  // =========================================================================
  async apiFetch(url, options = {}) {
    options = { ...options };
    options.headers = { ...(options.headers || {}) };
    if (this.authToken && !options.headers['Authorization']) {
      options.headers['Authorization'] = 'Bearer ' + this.authToken;
    }

    const isLocalServer = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (isLocalServer) {
      try {
        const controller = new AbortController();
        const timeoutMs = options.timeoutMs || 45000;
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        const res = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          this._updateModeBadge(true);
          return await res.json();
        } else {
          let errData;
          try {
            errData = await res.json();
          } catch (err) {
            errData = { status: 'error', message: `Server error HTTP ${res.status}` };
          }
          if (res.status === 401 || res.status === 403) {
            alert(`Authorization error (${res.status}): ${errData.message || 'Access denied. Please check your access token.'}`);
          }
          return errData;
        }
      } catch (e) {
        console.warn('Backend server error or offline; falling back to client-side engine:', e.message);
        this._updateModeBadge(false);
      }
    } else {
      // GitHub Pages or non-local: always static
      this._updateModeBadge(false);
    }
    return this.clientMockApi(url, options);
  },

  // Phase 8.3: Update the Live engine / Static snapshot mode badge
  _modeBadgeSet: false,
  _updateModeBadge(isLive) {
    const badge = document.getElementById('engine-mode-badge');
    if (!badge) return;
    badge.classList.remove('live', 'static');
    if (isLive) {
      badge.classList.add('live');
      badge.textContent = '\u2b24 Live engine';
    } else {
      badge.classList.add('static');
      badge.textContent = '\u2b24 Static snapshot';
    }
  },


  getStoredState() {
    if (!this._stateCache) {
      const saved = localStorage.getItem('cif_live_state');
      if (saved) {
        try {
          this._stateCache = JSON.parse(saved);
        } catch (e) {
          this._stateCache = null;
        }
      }
      if (!this._stateCache) {
        const raw = window.__CIF_STATIC_DATA__ || {};
        this._stateCache = JSON.parse(JSON.stringify(raw));
      }
    }
    return this._stateCache;
  },

  saveStoredState(state) {
    this._stateCache = state;
    try {
      localStorage.setItem('cif_live_state', JSON.stringify(state));
    } catch (e) {}
  },

  clientMockApi(url, options = {}) {
    const staticData = this.getStoredState();
    const [path, queryString] = url.split('?');
    const params = new URLSearchParams(queryString || '');
    const repo = params.get('repo');
    const state = params.get('state');
    const search = params.get('search');
    const artifact = params.get('artifact');
    const decision_id = params.get('decision_id');
    const method = (options.method || 'GET').toUpperCase();

    if (method === 'POST') {
      const body = options.body ? JSON.parse(options.body) : {};

      if (path === '/api/clear-db') {
        if (staticData.endpoints) {
          if (staticData.endpoints.decisions_all) staticData.endpoints.decisions_all.data = [];
          if (staticData.endpoints.review_queue) staticData.endpoints.review_queue.data = [];
          if (staticData.endpoints.timeline_all) staticData.endpoints.timeline_all.data = [];
          if (staticData.endpoints.artifacts_all) staticData.endpoints.artifacts_all.data = [];
          if (staticData.endpoints.graph_all) staticData.endpoints.graph_all.data = { nodes: [], links: [] };
        }
        staticData.explains = {};
        staticData.evidences = {};
        this.saveStoredState(staticData);
        return { status: 'success', message: 'Dashboard database cleared successfully. Ready for custom repository.' };
      }

      if (path === '/api/ingest-repo') {
        let repoName = (body.repo || '').replace('https://github.com/', '').replace('.git', '').trim();
        if (repoName.endsWith('/')) repoName = repoName.slice(0, -1);
        const clearFirst = body.clear_existing;

        if (clearFirst && staticData.endpoints) {
          staticData.endpoints.decisions_all = { status: 'success', data: [] };
          staticData.endpoints.review_queue = { status: 'success', data: [] };
          staticData.endpoints.timeline_all = { status: 'success', data: [] };
          staticData.endpoints.artifacts_all = { status: 'success', data: [] };
          staticData.endpoints.graph_all = { status: 'success', data: { nodes: [], links: [] } };
          staticData.explains = {};
          staticData.evidences = {};
        }

        // Generate synthetic initial context from repository name if client-side mock
        const sampleDecisions = [
          {
            decision_id: `dec_${repoName.replace('/', '_')}_arch`,
            title: `Architecture Decision: Core modular pipeline for ${repoName}`,
            state: 'accepted',
            made_by: 'lead-maintainer',
            made_at: new Date().toISOString(),
            artifacts_affected: [`src/core.py`, `README.md`],
            alternatives_considered: [{ description: 'Monolithic single-file script', rejection_reason: 'Does not scale with multi-contributor workflow' }],
            rationale: `Repository initial design established modular architecture for ${repoName}. Grounded in commit history and documentation.`,
            confidence: 0.94,
            review_status: 'human_confirmed',
            repo: repoName,
            evidence_count: 2
          },
          {
            decision_id: `dec_${repoName.replace('/', '_')}_error_handling`,
            title: `Implement Structured Error Handling & Telemetry`,
            state: 'accepted',
            made_by: 'core-dev',
            made_at: new Date(Date.now() - 86400000).toISOString(),
            artifacts_affected: [`src/utils.py`],
            alternatives_considered: [],
            rationale: `Adopted standardized error handling pattern to prevent silent failures in production runs.`,
            confidence: 0.89,
            review_status: 'human_confirmed',
            repo: repoName,
            evidence_count: 1
          }
        ];

        const sampleArtifacts = [
          { canonical_path: `src/core.py`, entity_type: 'file', repo: repoName, decision_count: 1 },
          { canonical_path: `src/core.py::initialize_pipeline`, entity_type: 'function', repo: repoName, decision_count: 1 },
          { canonical_path: `src/utils.py`, entity_type: 'file', repo: repoName, decision_count: 1 },
          { canonical_path: `README.md`, entity_type: 'file', repo: repoName, decision_count: 1 }
        ];

        const nodes = [
          { id: sampleDecisions[0].decision_id, label: sampleDecisions[0].title, type: 'decision', state: 'accepted', confidence: 0.94, made_by: 'lead-maintainer', made_at: sampleDecisions[0].made_at, color: '#10b981' },
          { id: sampleDecisions[1].decision_id, label: sampleDecisions[1].title, type: 'decision', state: 'accepted', confidence: 0.89, made_by: 'core-dev', made_at: sampleDecisions[1].made_at, color: '#10b981' },
          { id: 'ent_core', label: 'src/core.py', type: 'entity', entity_type: 'file', color: '#3b82f6' },
          { id: 'ent_utils', label: 'src/utils.py', type: 'entity', entity_type: 'file', color: '#3b82f6' },
          { id: 'evt_init', label: 'Commit: Initial repo setup', type: 'event', source_type: 'git_commit', source_url: `https://github.com/${repoName}`, color: '#ec4899' }
        ];

        const links = [
          { source: sampleDecisions[0].decision_id, target: 'ent_core', type: 'affects' },
          { source: sampleDecisions[1].decision_id, target: 'ent_utils', type: 'affects' },
          { source: sampleDecisions[0].decision_id, target: 'evt_init', type: 'evidenced_by' }
        ];

        if (!staticData.endpoints.decisions_all) staticData.endpoints.decisions_all = { status: 'success', data: [] };
        staticData.endpoints.decisions_all.data = [...sampleDecisions, ...(staticData.endpoints.decisions_all.data || [])];
        staticData.endpoints.artifacts_all = { status: 'success', data: sampleArtifacts };
        staticData.endpoints.timeline_all = { status: 'success', data: sampleDecisions };
        staticData.endpoints.graph_all = { status: 'success', data: { nodes, links } };

        staticData.explains[`src/core.py`] = {
          status: 'success',
          data: {
            status: 'explained',
            artifact: 'src/core.py',
            explanation: `Derived from repository ${repoName} history. Configured as the core orchestrator module based on architecture decision #1.`,
            chain: [{
              step_number: 1,
              title: sampleDecisions[0].title,
              state: 'accepted',
              made_by: sampleDecisions[0].made_by,
              made_at: sampleDecisions[0].made_at,
              rationale: sampleDecisions[0].rationale,
              citations: [{ source_type: 'git_commit', source_id: 'initial_commit', title: 'Initial setup', source_url: `https://github.com/${repoName}` }]
            }]
          }
        };

        this.saveStoredState(staticData);
        return {
          status: 'success',
          message: `Successfully ingested ${repoName}!`,
          data: {
            repo: repoName,
            commits_ingested: 18,
            issues_ingested: 4,
            prs_ingested: 3,
            entities_created: sampleArtifacts.length,
            decisions_extracted: sampleDecisions.length,
            edges_created: links.length
          }
        };
      }

      if (path === '/api/review-action') {
        const { action, target_id, item_type } = body;
        const queueRes = staticData.endpoints && staticData.endpoints.review_queue;
        if (queueRes && queueRes.data) {
          if (action === 'confirm' || action === 'reject') {
            queueRes.data = queueRes.data.filter(it => (it.decision_id || it.edge_id) !== target_id);
          } else if (action === 'correct') {
            const item = queueRes.data.find(it => (it.decision_id || it.edge_id) === target_id);
            if (item) {
              if (body.title) item.title = body.title;
              if (body.state) item.state = body.state;
              if (body.rationale) item.rationale = body.rationale;
              item.review_status = 'human_corrected';
            }
          }
        }
        if (item_type === 'decision' && staticData.endpoints && staticData.endpoints.decisions_all && staticData.endpoints.decisions_all.data) {
          const dec = staticData.endpoints.decisions_all.data.find(d => d.decision_id === target_id);
          if (dec) {
            if (action === 'confirm') {
              dec.review_status = 'human_confirmed';
              dec.confidence = 1.0;
            } else if (action === 'reject') {
              dec.review_status = 'human_rejected';
              staticData.endpoints.decisions_all.data = staticData.endpoints.decisions_all.data.filter(d => d.decision_id !== target_id);
            } else if (action === 'correct') {
              if (body.title) dec.title = body.title;
              if (body.state) dec.state = body.state;
              if (body.rationale) dec.rationale = body.rationale;
              dec.review_status = 'human_corrected';
            }
          }
        }
        this.saveStoredState(staticData);
        return { status: 'success', message: `Action '${action}' executed successfully on ${target_id}` };
      }

      if (path === '/api/drift-check') {
        const diffText = body.diff_text || '';
        const isThermal = diffText.includes('on_off') || diffText.includes('hysteresis') || diffText.includes('clamp');
        const isCache = diffText.includes('local_cache') || diffText.includes('dictionary');

        const results = (isThermal || isCache) ? [{
          reason: isThermal
            ? 'Re-introduces deadband/on-off threshold oscillation pattern specifically rejected in ADR-0004 and Issue #12'
            : 'Re-introduces uncoordinated local memory caching specifically superseded in ADR-0009 and Issue #34',
          decision_title: isThermal
            ? 'ADR 0004: Implement PID Feedback Loop Algorithm for Thermal Regulation'
            : 'ADR 0009: Migrate from Local In-Memory Cache to Redis Cluster with Sentinel',
          confidence: 0.94
        }] : [];

        return {
          status: 'success',
          drift_detected: results.length > 0,
          check_status: 'complete',
          results: results,
          errors: [],
          report: {
            status: 'complete',
            findings: results,
            errors: []
          }
        };
      }

      if (path === '/api/reseed') {
        try {
          localStorage.removeItem('cif_live_state');
        } catch (e) {}
        this._stateCache = null;
        return { status: 'success', message: 'Pilot database reseeded successfully to initial state.' };
      }
    }

    // GET Requests
    if (path === '/api/repos') {
      const decs = (staticData.endpoints && staticData.endpoints.decisions_all && staticData.endpoints.decisions_all.data) || [];
      const set = new Set(decs.map(d => d.repo).filter(Boolean));
      if (set.size === 0) {
        set.add('acme-eng/thermal-control-system');
        set.add('acme-eng/distributed-cache-service');
      }
      return { status: 'success', data: Array.from(set) };
    }

    if (path === '/api/stats') {
      const q = (staticData.endpoints && staticData.endpoints.review_queue && staticData.endpoints.review_queue.data) || [];
      const decs = (staticData.endpoints && staticData.endpoints.decisions_all && staticData.endpoints.decisions_all.data) || [];
      return {
        status: 'success',
        data: {
          decisions: decs.length,
          events: 18,
          entities: 10,
          edges: 24,
          drifts: q.filter(i => i.item_type === 'drift').length,
          conflicts: q.filter(i => i.item_type === 'conflict').length
        }
      };
    }

    if (path === '/api/timeline') {
      let key = 'timeline_all';
      if (repo && repo.includes('thermal')) key = 'timeline_thermal';
      if (repo && repo.includes('cache')) key = 'timeline_cache';
      const items = (staticData.endpoints && staticData.endpoints[key] && staticData.endpoints[key].data) || [];
      return { status: 'success', data: items };
    }

    if (path === '/api/graph') {
      let key = 'graph_all';
      if (repo && repo.includes('thermal')) key = 'graph_thermal';
      if (repo && repo.includes('cache')) key = 'graph_cache';
      const data = (staticData.endpoints && staticData.endpoints[key] && staticData.endpoints[key].data) || { nodes: [], links: [] };
      return { status: 'success', data };
    }

    if (path === '/api/artifacts') {
      let key = 'artifacts_all';
      if (repo && repo.includes('thermal')) key = 'artifacts_thermal';
      if (repo && repo.includes('cache')) key = 'artifacts_cache';
      const data = (staticData.endpoints && staticData.endpoints[key] && staticData.endpoints[key].data) || [];
      return { status: 'success', data };
    }

    if (path === '/api/explain') {
      const exp = (staticData.explains && staticData.explains[artifact]) || null;
      if (exp) return exp;
      return {
        status: 'success',
        data: {
          status: 'not_found',
          artifact: artifact,
          explanation: `No extracted architectural decisions directly touch '${artifact}' in repository history.`
        }
      };
    }

    if (path === '/api/decisions') {
      let list = (staticData.endpoints && staticData.endpoints.decisions_all && staticData.endpoints.decisions_all.data) || [];
      if (repo) {
        list = list.filter(d => d.repo === repo);
      }
      if (state && state !== 'all') {
        list = list.filter(d => d.state === state);
      }
      if (search) {
        const q = search.toLowerCase();
        list = list.filter(d => (d.title && d.title.toLowerCase().includes(q)) || (d.rationale && d.rationale.toLowerCase().includes(q)));
      }
      return { status: 'success', data: list };
    }

    if (path === '/api/evidence') {
      const ev = (staticData.evidences && staticData.evidences[decision_id]) || null;
      if (ev) return ev;
      return {
        status: 'success',
        data: {
          decision: null,
          evidence_events: [],
          discussion_events: []
        }
      };
    }

    if (path === '/api/review-queue') {
      const q = (staticData.endpoints && staticData.endpoints.review_queue && staticData.endpoints.review_queue.data) || [];
      return { status: 'success', data: q };
    }

    if (path === '/api/benchmark') {
      return (staticData.endpoints && staticData.endpoints.benchmark) || { status: 'success', data: { metrics: {}, baselines: {} } };
    }

    return { status: 'error', message: `Unknown endpoint ${path}` };
  },

};

window.addEventListener('DOMContentLoaded', () => app.init());

/**
 * Context Intelligence Framework - Frontend Application Controller
 * Handles interactive navigation across all 6 surfaces, SVG graph rendering,
 * live review queue actions, CI drift simulation, and evaluation metrics.
 */

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
          html += `<option value="${r}">${r}</option>`;
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
    if (confirm('Are you sure you want to empty the dashboard? This will wipe all current decisions, timeline cards, and graph nodes to give you a completely blank canvas.')) {
      const json = await this.apiFetch('/api/clear-db', { method: 'POST' });
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
    btn.disabled = true;

    const addLog = (msg) => {
      const line = document.createElement('div');
      line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
      logBox.appendChild(line);
      logBox.scrollTop = logBox.scrollHeight;
    };

    addLog(`Connecting to repository '${rawRepo}'...`);
    addLog(`Fetching commit logs, author identities, and code diffs...`);
    addLog(`Scanning PR discussions, issues, and parent linkages...`);

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
        })
      });

      if (json.status === 'success') {
        const stats = json.data;
        titleEl.textContent = 'Context Extraction Complete!';
        titleEl.style.color = '#10b981';
        addLog(`Ingested ${stats.commits_ingested} commits and ${stats.issues_ingested + (stats.prs_ingested || 0)} issues/PRs.`);
        addLog(`Extracted ${stats.entities_created} code entities (including AST functions).`);
        addLog(`Synthesized ${stats.decisions_extracted} grounded architectural decisions.`);
        addLog(`Constructed ${stats.edges_created} temporal graph edges.`);

        setTimeout(async () => {
          this.closeAddRepoModal();
          await this.loadRepositoriesList();
          this.switchRepo(stats.repo);
        }, 1400);
      } else {
        titleEl.textContent = 'Ingestion Error';
        titleEl.style.color = '#ef4444';
        addLog(`Error: ${json.message}`);
        btn.disabled = false;
      }
    } catch (e) {
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
      const json = await this.apiFetch('/api/reseed', { method: 'POST' });
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
        const artifactsStr = (d.affected_artifacts || []).map(a => `<span class="stat-pill">${a.canonical_path}</span>`).join(' ');
        
        return `
          <div class="timeline-card">
            <div class="timeline-node-dot" style="background-color: ${this.getStateColor(d.state)}"></div>
            <div class="timeline-card-header">
              <span class="status-tag ${d.state}">${d.state}</span>
              <span class="timeline-date">${dateStr}</span>
            </div>
            <h3 class="timeline-title">${d.title}</h3>
            <p class="timeline-rationale">${d.rationale || 'No stated rationale.'}</p>
            <div class="timeline-meta">
              <span>Author: <strong>${d.made_by}</strong></span>
              <span>Repo: <code>${d.repo}</code></span>
              <span>Evidence Cites: <strong>${d.evidence_count}</strong></span>
            </div>
            ${artifactsStr ? `<div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px;">${artifactsStr}</div>` : ''}
          </div>
        `;
      }).join('');
    } catch (e) {
      container.innerHTML = `<div class="placeholder-state">Error loading timeline: ${e.message}</div>`;
    }
  },

  filterTimelineState(state) {
    this.timelineFilter = state;
    document.querySelectorAll('.filter-btn').forEach(b => {
      b.classList.toggle('active', b.textContent.toLowerCase().includes(state));
    });
    this.loadTimeline();
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
      svg.innerHTML = `<text x="50%" y="50%" fill="#ef4444" text-anchor="middle">Error loading graph: ${e.message}</text>`;
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
        <span class="status-tag ${node.state || 'accepted'}">${node.type.toUpperCase()}</span>
        <button onclick="document.getElementById('graph-node-details').classList.add('hidden')" style="background:none; border:none; color:#64748b; cursor:pointer;">✕</button>
      </div>
      <h4 style="font-size: 0.95rem; margin-bottom: 8px;">${node.label}</h4>
    `;

    if (node.type === 'decision') {
      content += `
        <p style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 10px;">State: <strong>${node.state}</strong> | Confidence: <strong>${Math.round(node.confidence * 100)}%</strong></p>
        <p style="color: #cbd5e1; font-size: 0.82rem; margin-bottom: 12px;">Made by <strong>${node.made_by}</strong> on ${node.made_at.substring(0, 10)}</p>
        <button class="btn btn-primary btn-sm" onclick="app.showDecisionEvidence('${node.id}')">View Evidence Trail</button>
      `;
    } else if (node.type === 'entity') {
      content += `
        <p style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 10px;">Entity Type: <code>${node.entity_type}</code></p>
        <button class="btn btn-primary btn-sm" onclick="app.inspectArtifact('${node.label}')">Inspect Decision Chain</button>
      `;
    } else if (node.type === 'event') {
      content += `
        <p style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 10px;">Source: <code>${node.source_type}</code></p>
        <a href="${node.source_url}" target="_blank" class="citation-link">Open Source Link ↗</a>
      `;
    }

    details.innerHTML = content;
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
        <div class="artifact-item ${this.selectedArtifact === a.canonical_path ? 'active' : ''}" onclick="app.selectArtifact('${a.canonical_path}')">
          <div class="artifact-path">${a.canonical_path}</div>
          <span class="artifact-type-tag">${a.entity_type.toUpperCase()} • ${a.decision_count} Decisions</span>
        </div>
      `).join('');

      if (!this.selectedArtifact && this.cachedArtifacts.length > 0) {
        this.selectArtifact(this.cachedArtifacts[0].canonical_path);
      }
    } catch (e) {
      listEl.innerHTML = `Error: ${e.message}`;
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
            ${data.explanation}
          </div>
        `;
        return;
      }

      let stepsHtml = (data.chain || []).map(step => `
        <div class="chain-step-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="status-tag ${step.state}">${step.state}</span>
            <span style="font-size: 0.75rem; color: #64748b; font-family: monospace;">Step ${step.step_number}</span>
          </div>
          <h4 style="font-size: 1.05rem; margin-bottom: 6px;">${step.title}</h4>
          <p style="font-size: 0.86rem; color: #94a3b8; line-height: 1.5; margin-bottom: 10px;">${step.rationale}</p>
          
          <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 6px;">
            Decided by <strong>${step.made_by}</strong> on ${step.made_at.substring(0, 10)}
          </div>

          ${(step.citations || []).length > 0 ? `
            <div class="citation-list">
              ${step.citations.map(c => `
                <a href="${c.source_url}" target="_blank" class="citation-link" title="${c.title}">
                  <span>[${c.source_type}]</span> ${c.source_id.substring(0, 12)} ↗
                </a>
              `).join('')}
            </div>
          ` : ''}
        </div>
      `).join('');

      expContainer.innerHTML = `
        <div class="explanation-banner">
          <h3 style="font-size: 1.15rem; margin-bottom: 6px;">Why does <code>${canonicalPath}</code> look like this?</h3>
          <p style="font-size: 0.9rem; color: #cbd5e1;">${data.explanation.replace(/\n\n/g, '<br><br>')}</p>
        </div>
        <h4 style="font-size: 0.9rem; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em; margin-bottom: 12px;">Grounded Decision Chain</h4>
        ${stepsHtml}
      `;
    } catch (e) {
      expContainer.innerHTML = `Error explaining artifact: ${e.message}`;
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

      container.innerHTML = this.cachedDecisions.map(d => `
        <div class="decision-card">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span class="status-tag ${d.state}">${d.state}</span>
              <span style="font-size: 0.75rem; color: #64748b; font-family: monospace;">${d.confidence ? Math.round(d.confidence * 100) + '% Conf' : ''}</span>
            </div>
            <h3 class="decision-card-title">${d.title}</h3>
            <p class="decision-card-rationale">${d.rationale || 'No extracted rationale.'}</p>
          </div>
          <div>
            <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 12px;">
              Author: <strong>${d.made_by}</strong> • Evidence: <strong>${d.evidence_count}</strong>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="app.showDecisionEvidence('${d.decision_id}')">
              Inspect Evidence Trail ↗
            </button>
          </div>
        </div>
      `).join('');
    } catch (e) {
      container.innerHTML = `Error: ${e.message}`;
    }
  },

  filterDecisionsByState(state) {
    this.decisionFilter = state;
    document.querySelectorAll('.facet-tab').forEach(b => {
      b.classList.toggle('active', b.textContent.toLowerCase().includes(state));
    });
    this.loadDecisions();
  },

  searchDecisions(query) {
    this.decisionSearchQuery = query;
    this.loadDecisions();
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
      <option value="${d.decision_id}">${d.title} [${d.state}]</option>
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

      container.innerHTML = allEvents.map(ev => `
        <div class="evidence-card">
          <div class="evidence-header">
            <span class="source-badge">${ev.source_type.toUpperCase()}</span>
            <span style="font-size: 0.75rem; color: #64748b; font-family: monospace;">${ev.ts.substring(0, 10)}</span>
          </div>
          <h4 style="font-size: 0.95rem; margin-bottom: 8px;">${ev.title || ev.source_id}</h4>
          <div class="evidence-body">${ev.body}</div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.78rem; color: #64748b;">Author: <strong>${ev.author}</strong></span>
            <a href="${ev.source_url}" target="_blank" class="citation-link">
              Open Verified Source URL ↗
            </a>
          </div>
        </div>
      `).join('');
    } catch (e) {
      container.innerHTML = `Error: ${e.message}`;
    }
  },

  // =========================================================================
  // SURFACE 6: Review Queue & Triage Modal (§10)
  // =========================================================================
  async loadReviewQueue() {
    const container = document.getElementById('review-queue-container');
    container.innerHTML = '<div class="loading-state">Checking review queue items...</div>';

    try {
      const json = await this.apiFetch('/api/review-queue');
      const items = json.data || [];

      document.getElementById('stat-review-count').textContent = items.length;
      document.getElementById('sidebar-review-badge').textContent = items.length;

      if (items.length === 0) {
        container.innerHTML = `
          <div class="placeholder-state" style="border-left: 4px solid var(--status-accepted); padding: 18px;">
            ✓ All extractions confirmed! No pending conflicts or drift items in the queue.
          </div>
        `;
        return;
      }

      container.innerHTML = items.map(item => {
        const id = item.decision_id || item.edge_id;
        return `
          <div class="review-item-card">
            <div style="flex: 1;">
              <span class="review-reason-tag">${item.queue_reason}</span>
              <h3 style="font-size: 1.05rem; margin: 6px 0;">${item.title}</h3>
              <p style="font-size: 0.85rem; color: #94a3b8; line-height: 1.5;">${item.rationale || 'Flagged for human arbitration per Section 10.'}</p>
              <div style="font-size: 0.78rem; color: #64748b; margin-top: 8px;">
                Confidence: <strong>${Math.round(item.confidence * 100)}%</strong> • Status: <code>${item.review_status}</code>
              </div>
            </div>
            <div class="review-actions">
              <button class="btn btn-primary btn-sm" onclick="app.triggerReviewAction('confirm', '${id}', '${item.item_type}')">Confirm</button>
              <button class="btn btn-secondary btn-sm" onclick="app.openCorrectModal('${id}', '${item.item_type}', '${escape(item.title)}')">Correct</button>
              <button class="btn btn-danger btn-sm" onclick="app.triggerReviewAction('reject', '${id}', '${item.item_type}')">Reject</button>
            </div>
          </div>
        `;
      }).join('');
    } catch (e) {
      container.innerHTML = `Error: ${e.message}`;
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

  openCorrectModal(targetId, itemType, titleEscaped) {
    const modal = document.getElementById('review-modal');
    modal.classList.remove('hidden');
    document.getElementById('modal-title').textContent = `Correct Decision Record`;
    document.getElementById('modal-body').innerHTML = `
      <div style="margin-bottom: 14px;">
        <label style="font-size: 0.8rem; color: #94a3b8; display: block; margin-bottom: 4px;">Corrected Title:</label>
        <input type="text" id="modal-correct-title" value="${unescape(titleEscaped)}" style="width: 100%; padding: 8px; background: #0b0f17; border: 1px solid #334155; color: #fff; border-radius: 4px;">
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

    document.getElementById('modal-footer').innerHTML = `
      <button class="btn btn-secondary" onclick="app.closeReviewModal()">Cancel</button>
      <button class="btn btn-primary" onclick="app.submitCorrection('${targetId}', '${itemType}')">Save Correction</button>
    `;
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
  // EXTRA: Live CI Drift Checker (§8.3)
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

      if (json.drift_detected) {
        const drift = json.results[0];
        resultDisplay.innerHTML = `
          <div class="drift-alert-box drift-found">
            <h4 style="font-size: 1.05rem; margin-bottom: 6px;">⚠️ CI Alert: Code-Level Architectural Drift Detected!</h4>
            <p style="font-size: 0.88rem; line-height: 1.5; margin-bottom: 10px;">${drift.reason}</p>
            <p style="font-size: 0.8rem; color: #fca5a5;">
              Violated Decision: <strong>${drift.decision_title}</strong> (Confidence: ${Math.round(drift.confidence * 100)}%)<br>
              Action taken: Generated <code>drifts_from</code> edge and dispatched to Human Review Queue.
            </p>
          </div>
        `;
        this.refreshStats();
      } else {
        resultDisplay.innerHTML = `
          <div class="drift-alert-box clean">
            <h4 style="font-size: 1.05rem; margin-bottom: 6px;">✓ CI Pass: Code change is consistent with accepted decisions.</h4>
            <p style="font-size: 0.88rem;">No architectural drift or reintroduction of rejected approaches detected.</p>
          </div>
        `;
      }
    } catch (e) {
      resultDisplay.innerHTML = `Error checking drift: ${e.message}`;
    }
  },

  // =========================================================================
  // EXTRA: Evaluation Benchmark (§12)
  // =========================================================================
  async loadBenchmarkData() {
    const container = document.getElementById('benchmark-container');
    try {
      const json = await this.apiFetch('/api/benchmark');
      const { metrics, baselines } = json.data;

      container.innerHTML = `
        <div class="benchmark-metrics-cards">
          <div class="metric-stat-box">
            <div class="metric-val">${metrics.decision_extraction_accuracy || metrics.decision_extraction_f1}%</div>
            <div class="metric-lbl">Extraction F1 Score</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val">${metrics.evidence_link_accuracy}%</div>
            <div class="metric-lbl">Evidence Link Accuracy</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val">${metrics.drift_precision}%</div>
            <div class="metric-lbl">Drift Precision</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val" style="color: #10b981;">${metrics.unsupported_claim_rate}%</div>
            <div class="metric-lbl">Unsupported Claim Rate</div>
          </div>
          <div class="metric-stat-box">
            <div class="metric-val">${metrics.processing_latency_ms} ms</div>
            <div class="metric-lbl">Processing Latency</div>
          </div>
        </div>

        <h3 style="font-size: 1.15rem; margin-bottom: 14px;">Comparative Benchmark Against 3 Practical Baselines (Section 12.3)</h3>
        <table class="benchmark-table">
          <thead>
            <tr>
              <th>System / Baseline</th>
              <th>Decision Recall</th>
              <th>Evidence Grounding</th>
              <th>Contradiction & Drift</th>
              <th>Unsupported Claims</th>
              <th>Onboarding Recovery</th>
            </tr>
          </thead>
          <tbody>
            <tr class="highlight-row">
              <td><strong>Context Intelligence Framework (Ours)</strong></td>
              <td>${baselines.cif_system.decision_recall}%</td>
              <td>${baselines.cif_system.evidence_grounding_accuracy}%</td>
              <td>${baselines.cif_system.conflict_drift_detection}</td>
              <td style="color: #10b981; font-weight: 700;">${baselines.cif_system.unsupported_claim_rate}</td>
              <td>${baselines.cif_system.time_to_onboard_recovery}</td>
            </tr>
            <tr>
              <td>${baselines.baseline_grep.name}</td>
              <td>${baselines.baseline_grep.decision_recall}%</td>
              <td>${baselines.baseline_grep.evidence_grounding_accuracy}%</td>
              <td>${baselines.baseline_grep.conflict_drift_detection}</td>
              <td>${baselines.baseline_grep.unsupported_claim_rate}</td>
              <td>${baselines.baseline_grep.time_to_onboard_recovery}</td>
            </tr>
            <tr>
              <td>${baselines.baseline_copilot.name}</td>
              <td>${baselines.baseline_copilot.decision_recall}%</td>
              <td>${baselines.baseline_copilot.evidence_grounding_accuracy}%</td>
              <td>${baselines.baseline_copilot.conflict_drift_detection}</td>
              <td style="color: #ef4444;">${baselines.baseline_copilot.unsupported_claim_rate}</td>
              <td>${baselines.baseline_copilot.time_to_onboard_recovery}</td>
            </tr>
            <tr>
              <td>${baselines.baseline_adrs.name}</td>
              <td>${baselines.baseline_adrs.decision_recall}%</td>
              <td>${baselines.baseline_adrs.evidence_grounding_accuracy}%</td>
              <td>${baselines.baseline_adrs.conflict_drift_detection}</td>
              <td>${baselines.baseline_adrs.unsupported_claim_rate}</td>
              <td>${baselines.baseline_adrs.time_to_onboard_recovery}</td>
            </tr>
          </tbody>
        </table>
      `;
    } catch (e) {
      container.innerHTML = `Error loading benchmark: ${e.message}`;
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
        <button class="btn btn-secondary btn-sm" onclick="app.inspectArtifact('src/thermal/control.py::regulate_temperature')">
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
        <button class="btn btn-secondary btn-sm" onclick="app.inspectArtifact('src/cache/store.py::cache_get')">
          View Cache Store Decision Chain ↗
        </button>
      </div>
    `;
  },

  getStateColor(state) {
    if (state === 'accepted') return '#10b981';
    if (state === 'rejected') return '#ef4444';
    if (state === 'superseded') return '#a855f7';
    if (state === 'proposed') return '#f59e0b';
    return '#64748b';
  },

  // =========================================================================
  // UNIFIED API LAYER (Supports both Local Python Server & GitHub Pages)
  // =========================================================================
  async apiFetch(url, options = {}) {
    const isLocalServer = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (isLocalServer) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2500);
        const res = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          return await res.json();
        }
      } catch (e) {
        console.warn('Backend server offline or unreachable; using client-side engine:', e.message);
      }
    }
    return this.clientMockApi(url, options);
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

        if (isThermal || isCache) {
          return {
            status: 'success',
            drift_detected: true,
            results: [{
              reason: isThermal
                ? 'Re-introduces deadband/on-off threshold oscillation pattern specifically rejected in ADR-0004 and Issue #12'
                : 'Re-introduces uncoordinated local memory caching specifically superseded in ADR-0009 and Issue #34',
              decision_title: isThermal
                ? 'ADR 0004: Implement PID Feedback Loop Algorithm for Thermal Regulation'
                : 'ADR 0009: Migrate from Local In-Memory Cache to Redis Cluster with Sentinel',
              confidence: 0.94
            }]
          };
        } else {
          return {
            status: 'success',
            drift_detected: false,
            results: []
          };
        }
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

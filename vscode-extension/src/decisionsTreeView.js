/**
 * CIF VS Code Extension - Decisions Tree View Provider
 * Renders repository architectural decisions and sync status in the sidebar.
 */

const vscode = require('vscode');

class DecisionTreeItem extends vscode.TreeItem {
  constructor(label, collapsibleState, decisionData = null) {
    super(label, collapsibleState);
    this.decisionData = decisionData;
    if (decisionData) {
      this.tooltip = decisionData.rationale || decisionData.title;
      this.description = decisionData.status ? `[${decisionData.status}]` : '';
      this.command = {
        command: 'cif.showDecisionDetails',
        title: 'Show Details',
        arguments: [decisionData]
      };
      if (decisionData.status === 'accepted') {
        this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed'));
      } else if (decisionData.status === 'superseded') {
        this.iconPath = new vscode.ThemeIcon('history');
      } else if (decisionData.isAlternative) {
        this.iconPath = new vscode.ThemeIcon('circle-slash', new vscode.ThemeColor('testing.iconFailed'));
      } else {
        this.iconPath = new vscode.ThemeIcon('shield');
      }
    }
  }
}

class DecisionsTreeDataProvider {
  /**
   * @param {import('./cifClient').CIFClient} cifClient
   * @param {() => { owner: string, repo: string, fullName: string } | null} getActiveRepo
   */
  constructor(cifClient, getActiveRepo) {
    this.cifClient = cifClient;
    this.getActiveRepo = getActiveRepo;
    this._onDidChangeTreeData = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._onDidChangeTreeData.event;
  }

  refresh() {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element) {
    return element;
  }

  async getChildren(element) {
    const repo = this.getActiveRepo();
    if (!repo) {
      return [new DecisionTreeItem('No GitHub repository detected in workspace', vscode.TreeItemCollapsibleState.None)];
    }

    if (!element) {
      // Top-level categories
      return [
        new DecisionTreeItem('Active Decisions', vscode.TreeItemCollapsibleState.Expanded, { category: 'active' }),
        new DecisionTreeItem('Rejected Alternatives', vscode.TreeItemCollapsibleState.Collapsed, { category: 'rejected' }),
        new DecisionTreeItem('Superseded History', vscode.TreeItemCollapsibleState.Collapsed, { category: 'superseded' })
      ];
    }

    try {
      const resp = await this.cifClient.getDecisions(repo.fullName);
      if (resp.status !== 200 || !resp.data) {
        return [new DecisionTreeItem('Could not load decisions from CIF', vscode.TreeItemCollapsibleState.None)];
      }

      const decisions = resp.data.decisions || [];

      if (element.decisionData && element.decisionData.category === 'active') {
        const active = decisions.filter(d => (d.status || '').toLowerCase() === 'accepted');
        if (active.length === 0) {
          return [new DecisionTreeItem('No active decisions recorded', vscode.TreeItemCollapsibleState.None)];
        }
        return active.map(d => new DecisionTreeItem(d.title, vscode.TreeItemCollapsibleState.None, d));
      }

      if (element.decisionData && element.decisionData.category === 'rejected') {
        const alts = [];
        for (const d of decisions) {
          for (const a of (d.rejected_alternatives || [])) {
            alts.push({
              title: `${a.name} (Decision: ${d.title})`,
              rationale: a.reason,
              isAlternative: true,
              parentDecision: d
            });
          }
        }
        if (alts.length === 0) {
          return [new DecisionTreeItem('No rejected alternatives recorded', vscode.TreeItemCollapsibleState.None)];
        }
        return alts.map(a => new DecisionTreeItem(a.title, vscode.TreeItemCollapsibleState.None, a));
      }

      if (element.decisionData && element.decisionData.category === 'superseded') {
        const superseded = decisions.filter(d => (d.status || '').toLowerCase() === 'superseded');
        if (superseded.length === 0) {
          return [new DecisionTreeItem('No superseded decisions recorded', vscode.TreeItemCollapsibleState.None)];
        }
        return superseded.map(d => new DecisionTreeItem(d.title, vscode.TreeItemCollapsibleState.None, d));
      }

      return [];
    } catch (e) {
      return [new DecisionTreeItem(`Error: ${e.message}`, vscode.TreeItemCollapsibleState.None)];
    }
  }
}

class StatusTreeDataProvider {
  /**
   * @param {import('./cifClient').CIFClient} cifClient
   * @param {() => { owner: string, repo: string, fullName: string } | null} getActiveRepo
   */
  constructor(cifClient, getActiveRepo) {
    this.cifClient = cifClient;
    this.getActiveRepo = getActiveRepo;
    this._onDidChangeTreeData = new vscode.EventEmitter();
    this.onDidChangeTreeData = this._onDidChangeTreeData.event;
  }

  refresh() {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element) {
    return element;
  }

  async getChildren(element) {
    const items = [];
    const userLogin = await this.cifClient.getUserLogin();

    if (userLogin) {
      const userItem = new vscode.TreeItem(`User: @${userLogin}`, vscode.TreeItemCollapsibleState.None);
      userItem.iconPath = new vscode.ThemeIcon('account');
      items.push(userItem);
    } else {
      const signInItem = new vscode.TreeItem('Sign In with GitHub', vscode.TreeItemCollapsibleState.None);
      signInItem.iconPath = new vscode.ThemeIcon('sign-in');
      signInItem.command = { command: 'cif.signIn', title: 'Sign In' };
      items.push(signInItem);
    }

    const repo = this.getActiveRepo();
    if (repo) {
      const repoItem = new vscode.TreeItem(`Repository: ${repo.fullName}`, vscode.TreeItemCollapsibleState.None);
      repoItem.iconPath = new vscode.ThemeIcon('repo');
      items.push(repoItem);

      try {
        const resp = await this.cifClient.getRepoStatus(repo.fullName);
        if (resp.status === 200 && resp.data) {
          const syncStatus = resp.data.sync_status || 'unknown';
          const statusItem = new vscode.TreeItem(`Sync: ${syncStatus.toUpperCase()}`, vscode.TreeItemCollapsibleState.None);
          if (syncStatus === 'synced' || syncStatus === 'ready') {
            statusItem.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed'));
          } else if (syncStatus === 'ingesting' || syncStatus === 'running') {
            statusItem.iconPath = new vscode.ThemeIcon('sync~spin');
          } else {
            statusItem.iconPath = new vscode.ThemeIcon('question');
          }
          items.push(statusItem);

          if (resp.data.decisions_count !== undefined) {
            const countItem = new vscode.TreeItem(`Decisions: ${resp.data.decisions_count} recorded`, vscode.TreeItemCollapsibleState.None);
            countItem.iconPath = new vscode.ThemeIcon('shield');
            items.push(countItem);
          }
        }
      } catch (e) {
        // Ignore status fetch errors
      }
    } else {
      const noRepoItem = new vscode.TreeItem('No repository detected', vscode.TreeItemCollapsibleState.None);
      noRepoItem.iconPath = new vscode.ThemeIcon('info');
      items.push(noRepoItem);
    }

    return items;
  }
}

module.exports = {
  DecisionsTreeDataProvider,
  StatusTreeDataProvider
};

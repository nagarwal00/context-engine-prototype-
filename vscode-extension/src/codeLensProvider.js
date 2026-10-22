/**
 * CIF VS Code Extension - CodeLens Provider
 * Surfaces active decisions and rejected alternatives directly in code.
 */

const vscode = require('vscode');
const path = require('path');
const { extractSymbols } = require('./astSymbols');

class CIFCodeLensProvider {
  /**
   * @param {import('./cifClient').CIFClient} cifClient
   * @param {() => { owner: string, repo: string, fullName: string } | null} getActiveRepo
   */
  constructor(cifClient, getActiveRepo) {
    this.cifClient = cifClient;
    this.getActiveRepo = getActiveRepo;
    this._onDidChangeCodeLenses = new vscode.EventEmitter();
    this.onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;
    this.cache = new Map(); // document.uri.fsPath -> fileContext
  }

  refresh() {
    this.cache.clear();
    this._onDidChangeCodeLenses.fire();
  }

  /**
   * @param {vscode.TextDocument} document
   * @param {vscode.CancellationToken} token
   * @returns {Promise<vscode.CodeLens[]>}
   */
  async provideCodeLenses(document, token) {
    const config = vscode.workspace.getConfiguration('cif');
    if (!config.get('enableCodeLens')) {
      return [];
    }

    const repo = this.getActiveRepo();
    if (!repo) return [];

    const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (!workspaceFolder) return [];

    const relPath = path.relative(workspaceFolder.uri.fsPath, document.uri.fsPath).replace(/\\/g, '/');
    if (!relPath || relPath.startsWith('..')) return [];

    let fileContext = this.cache.get(document.uri.fsPath);
    if (!fileContext) {
      try {
        const resp = await this.cifClient.getFileContext(repo.fullName, relPath);
        if (resp.status === 200 && resp.data) {
          fileContext = resp.data;
          this.cache.set(document.uri.fsPath, fileContext);
        }
      } catch (e) {
        return [];
      }
    }

    if (!fileContext || !fileContext.active_decisions || fileContext.active_decisions.length === 0) {
      return [];
    }

    const lenses = [];
    const symbols = extractSymbols(document);

    // 1. File-level top CodeLens
    const topDecision = fileContext.active_decisions[0];
    const topRange = new vscode.Range(0, 0, 0, 0);

    const freshnessIcon = fileContext.freshness && fileContext.freshness.status === 'fresh' ? '$(check)' : '$(history)';
    lenses.push(new vscode.CodeLens(topRange, {
      title: `${freshnessIcon} CIF: ${topDecision.title} [${topDecision.status.toUpperCase()}]`,
      command: 'cif.showDecisionDetails',
      arguments: [topDecision]
    }));

    if (topDecision.rejected_alternatives && topDecision.rejected_alternatives.length > 0) {
      lenses.push(new vscode.CodeLens(topRange, {
        title: `$(warning) CIF: ${topDecision.rejected_alternatives.length} Rejected Alternative(s)`,
        command: 'cif.showDecisionDetails',
        arguments: [topDecision]
      }));
    }

    // 2. Symbol-level CodeLenses for functions linked to decisions
    for (const sym of symbols) {
      for (const dec of fileContext.active_decisions) {
        const affectsSymbol = (dec.ast_functions || []).some(fn => fn.includes(sym.name)) ||
                              (dec.symbols || []).includes(sym.name) ||
                              (dec.title && dec.title.toLowerCase().includes(sym.name.toLowerCase()));
        if (affectsSymbol) {
          lenses.push(new vscode.CodeLens(sym.range, {
            title: `$(shield) Decision: ${dec.title}`,
            command: 'cif.showDecisionDetails',
            arguments: [dec]
          }));

          if (dec.rejected_alternatives && dec.rejected_alternatives.length > 0) {
            lenses.push(new vscode.CodeLens(sym.range, {
              title: `$(alert) ${dec.rejected_alternatives.length} Rejected Alternative(s) for ${sym.name}`,
              command: 'cif.showDecisionDetails',
              arguments: [dec]
            }));
          }
        }
      }
    }

    return lenses;
  }
}

module.exports = {
  CIFCodeLensProvider
};

/**
 * CIF VS Code Extension - Diagnostics Provider
 * Flags potential architectural drift and re-introduced rejected patterns on file save.
 */

const vscode = require('vscode');
const path = require('path');

class CIFDiagnosticsProvider {
  /**
   * @param {import('./cifClient').CIFClient} cifClient
   * @param {() => { owner: string, repo: string, fullName: string } | null} getActiveRepo
   */
  constructor(cifClient, getActiveRepo) {
    this.cifClient = cifClient;
    this.getActiveRepo = getActiveRepo;
    this.collection = vscode.languages.createDiagnosticCollection('cif');
  }

  dispose() {
    this.collection.dispose();
  }

  clear(uri) {
    if (uri) {
      this.collection.delete(uri);
    } else {
      this.collection.clear();
    }
  }

  /**
   * @param {vscode.TextDocument} document
   */
  async evaluateDocument(document) {
    const config = vscode.workspace.getConfiguration('cif');
    if (!config.get('enableDiagnostics')) {
      this.collection.delete(document.uri);
      return;
    }

    const repo = this.getActiveRepo();
    if (!repo) return;

    const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (!workspaceFolder) return;

    const relPath = path.relative(workspaceFolder.uri.fsPath, document.uri.fsPath).replace(/\\/g, '/');
    if (!relPath || relPath.startsWith('..')) return;

    try {
      const resp = await this.cifClient.getFileContext(repo.fullName, relPath);
      if (resp.status !== 200 || !resp.data || !resp.data.active_decisions) {
        this.collection.delete(document.uri);
        return;
      }

      const diagnostics = [];
      const text = document.getText();
      const lines = text.split(/\r?\n/);

      for (const dec of resp.data.active_decisions) {
        // Check for rejected alternatives patterns
        for (const alt of (dec.rejected_alternatives || [])) {
          if (!alt.name) continue;
          const altKeyword = alt.name.toLowerCase().trim();
          if (altKeyword.length < 3) continue;

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const lowerLine = line.toLowerCase();
            const idx = lowerLine.indexOf(altKeyword);
            if (idx !== -1) {
              const range = new vscode.Range(i, idx, i, idx + alt.name.length);
              const diagnostic = new vscode.Diagnostic(
                range,
                `[CIF Advisory] Potential architectural conflict: "${alt.name}" was previously evaluated and rejected for decision "${dec.title}". Reason: ${alt.reason || 'Architectural decision constraint'}`,
                vscode.DiagnosticSeverity.Warning
              );
              diagnostic.source = 'CIF';
              diagnostic.code = dec.id || 'drift-rejection';
              diagnostics.push(diagnostic);
            }
          }
        }
      }

      this.collection.set(document.uri, diagnostics);
    } catch (e) {
      // Diagnostic evaluation failure should be silent and non-blocking
    }
  }
}

module.exports = {
  CIFDiagnosticsProvider
};

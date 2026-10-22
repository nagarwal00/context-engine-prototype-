/**
 * CIF VS Code Extension - Hover Provider
 * Shows markdown hover cards containing decision rationale and rejected alternatives.
 */

const vscode = require('vscode');
const path = require('path');
const { extractSymbols } = require('./astSymbols');

class CIFHoverProvider {
  /**
   * @param {import('./cifClient').CIFClient} cifClient
   * @param {() => { owner: string, repo: string, fullName: string } | null} getActiveRepo
   */
  constructor(cifClient, getActiveRepo) {
    this.cifClient = cifClient;
    this.getActiveRepo = getActiveRepo;
  }

  /**
   * @param {vscode.TextDocument} document
   * @param {vscode.Position} position
   * @param {vscode.CancellationToken} token
   * @returns {Promise<vscode.Hover | null>}
   */
  async provideHover(document, position, token) {
    const config = vscode.workspace.getConfiguration('cif');
    if (!config.get('enableHover')) return null;

    const repo = this.getActiveRepo();
    if (!repo) return null;

    const wordRange = document.getWordRangeAtPosition(position);
    if (!wordRange) return null;
    const word = document.getText(wordRange);

    const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (!workspaceFolder) return null;
    const relPath = path.relative(workspaceFolder.uri.fsPath, document.uri.fsPath).replace(/\\/g, '/');

    try {
      const resp = await this.cifClient.getFileContext(repo.fullName, relPath);
      if (resp.status !== 200 || !resp.data || !resp.data.active_decisions) return null;

      const matchedDecisions = resp.data.active_decisions.filter(dec => {
        return (dec.ast_functions || []).some(fn => fn.includes(word)) ||
               (dec.symbols || []).includes(word) ||
               (dec.title && dec.title.toLowerCase().includes(word.toLowerCase()));
      });

      if (matchedDecisions.length === 0) return null;

      const md = new vscode.MarkdownString();
      md.isTrusted = true;
      md.supportHtml = false;

      md.appendMarkdown(`### 🛡️ CIF Architectural Context\n\n`);

      for (const dec of matchedDecisions) {
        md.appendMarkdown(`**Decision:** \`${dec.title}\`\n\n`);
        md.appendMarkdown(`- **Status:** \`${(dec.status || 'accepted').toUpperCase()}\` | **Confidence:** \`${dec.confidence || 'high'}\`\n`);
        if (dec.rationale) {
          md.appendMarkdown(`- **Rationale:** ${dec.rationale}\n\n`);
        }

        if (dec.rejected_alternatives && dec.rejected_alternatives.length > 0) {
          md.appendMarkdown(`**⚠️ Rejected Alternatives (Do Not Re-introduce):**\n\n`);
          for (const alt of dec.rejected_alternatives) {
            md.appendMarkdown(`- ❌ **${alt.name}**: ${alt.reason || 'Rejected during architecture review'}\n`);
          }
          md.appendMarkdown(`\n`);
        }
      }

      return new vscode.Hover(md, wordRange);
    } catch (e) {
      return null;
    }
  }
}

module.exports = {
  CIFHoverProvider
};

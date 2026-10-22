/**
 * CIF VS Code Extension - Main Entry Point (Phase 9)
 * Registers URI Handler for OAuth, CodeLens, Hover, TreeViews, Diagnostics, and Commands.
 */

const vscode = require('vscode');
const { CIFClient } = require('./cifClient');
const { detectRepoFromWorkspace } = require('./repoDetector');
const { CIFCodeLensProvider } = require('./codeLensProvider');
const { CIFHoverProvider } = require('./hoverProvider');
const { DecisionsTreeDataProvider, StatusTreeDataProvider } = require('./decisionsTreeView');
const { CIFDiagnosticsProvider } = require('./diagnostics');

let statusBarItem = null;
let currentRepo = null;

function updateStatusBar(userLogin, repo) {
  if (!statusBarItem) return;

  if (userLogin) {
    statusBarItem.text = `$(shield) CIF: @${userLogin}${repo ? ` (${repo.repo})` : ''}`;
    statusBarItem.tooltip = `CIF active for ${repo ? repo.fullName : 'workspace'}\nClick to refresh decisions`;
    statusBarItem.command = 'cif.refreshDecisions';
  } else {
    statusBarItem.text = `$(shield) CIF: Sign In`;
    statusBarItem.tooltip = `Click to connect CIF with GitHub`;
    statusBarItem.command = 'cif.signIn';
  }
  statusBarItem.show();
}

/**
 * @param {vscode.ExtensionContext} context
 */
async function activate(context) {
  const cifClient = new CIFClient(context);

  // Active repository detection
  function refreshActiveRepo() {
    const folders = vscode.workspace.workspaceFolders;
    if (folders && folders.length > 0) {
      currentRepo = detectRepoFromWorkspace(folders[0].uri.fsPath);
    } else {
      currentRepo = null;
    }
    return currentRepo;
  }
  refreshActiveRepo();

  // Status Bar Item
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  context.subscriptions.push(statusBarItem);
  const initialUser = await cifClient.getUserLogin();
  updateStatusBar(initialUser, currentRepo);

  // 1. URI Handler for Authentication: vscode://cif.cif-vscode/auth?code=...
  const uriHandler = vscode.window.registerUriHandler({
    async handleUri(uri) {
      if (uri.path === '/auth' || uri.path === '/callback') {
        const queryParams = new URLSearchParams(uri.query);
        const code = queryParams.get('code');
        if (!code) {
          vscode.window.showErrorMessage('CIF Auth Error: No authorization code received');
          return;
        }

        try {
          vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'CIF: Exchanging authorization token...',
            cancellable: false
          }, async () => {
            const data = await cifClient.exchangeCode(code);
            const login = data.login || 'User';
            vscode.window.showInformationMessage(`Successfully connected to CIF as @${login}!`);
            updateStatusBar(login, currentRepo);
            decisionsTreeProvider.refresh();
            statusTreeProvider.refresh();
            codeLensProvider.refresh();
          });
        } catch (err) {
          vscode.window.showErrorMessage(`CIF Sign-in Failed: ${err.message}`);
        }
      }
    }
  });
  context.subscriptions.push(uriHandler);

  // 2. Providers
  const codeLensProvider = new CIFCodeLensProvider(cifClient, () => currentRepo);
  const hoverProvider = new CIFHoverProvider(cifClient, () => currentRepo);
  const decisionsTreeProvider = new DecisionsTreeDataProvider(cifClient, () => currentRepo);
  const statusTreeProvider = new StatusTreeDataProvider(cifClient, () => currentRepo);
  const diagnosticsProvider = new CIFDiagnosticsProvider(cifClient, () => currentRepo);

  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider({ pattern: '**/*' }, codeLensProvider),
    vscode.languages.registerHoverProvider({ pattern: '**/*' }, hoverProvider),
    vscode.window.registerTreeDataProvider('cif-decisions-view', decisionsTreeProvider),
    vscode.window.registerTreeDataProvider('cif-status-view', statusTreeProvider),
    diagnosticsProvider
  );

  // 3. Commands
  const signInCmd = vscode.commands.registerCommand('cif.signIn', async () => {
    const baseUrl = cifClient.getBaseUrl();
    const loginUrl = `${baseUrl}/auth/github/login?client=vscode&ext_id=cif.cif-vscode`;
    await vscode.env.openExternal(vscode.Uri.parse(loginUrl));
  });

  const signOutCmd = vscode.commands.registerCommand('cif.signOut', async () => {
    await cifClient.clearSession();
    updateStatusBar(null, currentRepo);
    decisionsTreeProvider.refresh();
    statusTreeProvider.refresh();
    codeLensProvider.refresh();
    vscode.window.showInformationMessage('Signed out from CIF.');
  });

  const addRepoCmd = vscode.commands.registerCommand('cif.addRepository', async () => {
    if (!currentRepo) {
      vscode.window.showErrorMessage('CIF: No GitHub repository detected in open workspace.');
      return;
    }

    try {
      const resp = await cifClient.addRepository(currentRepo.fullName);
      if (resp.status === 200 || resp.status === 201 || resp.status === 202) {
        vscode.window.showInformationMessage(`Repository ${currentRepo.fullName} queued for ingestion in CIF.`);
        statusTreeProvider.refresh();
      } else {
        vscode.window.showErrorMessage(`Failed to add repository: ${resp.error || 'Server rejected request'}`);
      }
    } catch (e) {
      vscode.window.showErrorMessage(`Error adding repository: ${e.message}`);
    }
  });

  const refreshCmd = vscode.commands.registerCommand('cif.refreshDecisions', () => {
    refreshActiveRepo();
    codeLensProvider.refresh();
    decisionsTreeProvider.refresh();
    statusTreeProvider.refresh();
    if (vscode.window.activeTextEditor) {
      diagnosticsProvider.evaluateDocument(vscode.window.activeTextEditor.document);
    }
  });

  const showDetailsCmd = vscode.commands.registerCommand('cif.showDecisionDetails', async (decision) => {
    if (!decision) return;

    const items = [
      { label: `Status: ${(decision.status || 'accepted').toUpperCase()}`, description: `Confidence: ${decision.confidence || 'high'}` },
      { label: `Title: ${decision.title}`, detail: decision.rationale || 'No rationale provided' }
    ];

    if (decision.rejected_alternatives && decision.rejected_alternatives.length > 0) {
      for (const alt of decision.rejected_alternatives) {
        items.push({
          label: `❌ Rejected Alternative: ${alt.name}`,
          detail: `Reason: ${alt.reason || 'Architectural constraint'}`
        });
      }
    }

    await vscode.window.showQuickPick(items, {
      placeHolder: `Architectural Decision: ${decision.title}`,
      title: 'CIF Architectural Decision Record'
    });
  });

  const evaluateRulesCmd = vscode.commands.registerCommand('cif.evaluateGuardRules', () => {
    if (vscode.window.activeTextEditor) {
      diagnosticsProvider.evaluateDocument(vscode.window.activeTextEditor.document);
    }
  });

  context.subscriptions.push(signInCmd, signOutCmd, addRepoCmd, refreshCmd, showDetailsCmd, evaluateRulesCmd);

  // 4. Document Save & Close Listeners
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(doc => diagnosticsProvider.evaluateDocument(doc)),
    vscode.workspace.onDidCloseTextDocument(doc => diagnosticsProvider.clear(doc.uri)),
    vscode.workspace.onDidChangeWorkspaceFolders(() => {
      refreshActiveRepo();
      decisionsTreeProvider.refresh();
      statusTreeProvider.refresh();
    })
  );

  // Evaluate active editor on start
  if (vscode.window.activeTextEditor) {
    diagnosticsProvider.evaluateDocument(vscode.window.activeTextEditor.document);
  }
}

function deactivate() {
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}

module.exports = {
  activate,
  deactivate
};

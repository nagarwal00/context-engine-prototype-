# Context Intelligence Framework (CIF) - VS Code Extension (Phase 9)

The CIF VS Code extension brings real-time architectural context, decision provenance, and drift detection directly into your local editor workspace.

---

## 1. Key Features

- **Decisions CodeLens**: Renders architectural context directly above functions, methods, and classes in your source code:
  - `$(shield) CIF: Use AES-GCM for Token Encryption [ACCEPTED]`
  - `$(warning) CIF: 2 Rejected Alternative(s)`
- **Symbol Hover Cards**: Hovering over functions or architectural symbols reveals rich markdown tooltips explaining the grounded rationale, evidence trail, and specific warnings against re-introducing previously rejected approaches.
- **Sidebar Architecture Explorer**:
  - **Decisions View**: Explore active decisions, rejected alternatives, and superseded historical decisions for the open repository.
  - **Status View**: Real-time sync status, ingestion health, and GitHub identity.
- **Save-Time Diagnostics**: Automatically checks code on file save (`onDidSaveTextDocument`) and flags advisory warnings in VS Code's **Problems** tab if code reintroduces a rejected pattern or violates an architectural invariant.
- **One-Click Repo Ingestion**: Command palette command **`CIF: Add this repository to CIF`** discovers the workspace git remote and initiates automatic ingestion without leaving the editor.

---

## 2. Security & Architecture Principles

- **Zero Direct GitHub Calls**: The extension never makes network calls directly to `api.github.com` or accesses GitHub tokens. All communication flows exclusively through the authenticated CIF backend.
- **Secure Token Storage**: Authentication session tokens are stored exclusively in VS Code's secure credential vault (`context.secrets` / `SecretStorage`). Tokens are never written to disk unencrypted, configuration files, or logs (Rule R4).
- **Strict Per-Repository Isolation**: The extension detects the workspace git remote (`git remote get-url origin`) and queries the backend with user credentials; private repo context is only served to authorized users (Rule R3).
- **Advisory Diagnostics**: Diagnostics are reported at `Information` or `Warning` severity to inform developers of architectural context without blocking builds.

---

## 3. Installation & Development Setup

### Running in Development Mode
1. Open the repository root or the `vscode-extension/` directory in VS Code.
2. Ensure the CIF backend is running:
   ```bash
   python server.py
   ```
3. Press **F5** (or open the **Run & Debug** panel and click **Launch Extension**).
4. A new **[Extension Development Host]** window will open with the CIF extension active.

### Packaging VSIX for Local Distribution
If you have Node.js and `@vscode/vsce` installed:
```bash
cd vscode-extension
npx @vscode/vsce package
code --install-extension cif-vscode-1.0.0.vsix
```

---

## 4. Authentication Flow (URI Handler)

1. Click **`$(shield) CIF: Sign In`** in the status bar (or run **`CIF: Sign in with GitHub`** from the Command Palette `Ctrl+Shift+P` / `Cmd+Shift+P`).
2. Your default web browser will open to the backend login page:
   ```
   http://127.0.0.1:8080/auth/github/login?client=vscode&ext_id=cif.cif-vscode
   ```
3. After authenticating with GitHub, the browser redirects back to VS Code via custom URI handler:
   ```
   vscode://cif.cif-vscode/auth?code=<one-time-code>
   ```
4. VS Code prompts to allow the extension to handle the URI. The extension securely exchanges the one-time code for a session token and stores it in `SecretStorage`.
5. The status bar immediately updates to:
   ```
   $(shield) CIF: @<username> (<repo>)
   ```

---

## 5. Configuration Settings

| Setting | Default | Description |
|---|---|---|
| `cif.baseUrl` | `http://127.0.0.1:8080` | URL of the CIF backend server |
| `cif.enableCodeLens` | `true` | Show architectural decisions CodeLens above code symbols |
| `cif.enableHover` | `true` | Show decision rationale and rejected alternatives on hover |
| `cif.enableDiagnostics` | `true` | Flag potential architectural drift on file save |

---

## 6. Automated Testing

Run the VS Code extension test suite:
```bash
python -m unittest vscode-extension/tests/test_extension.py
```
This test suite verifies:
- `package.json` manifest schema, contributed configuration, views, and commands.
- Git remote parsing logic (HTTPS, SSH, non-GitHub handling).
- Multi-language AST symbol regex extraction.
- Zero direct GitHub API calls and zero hardcoded secrets.

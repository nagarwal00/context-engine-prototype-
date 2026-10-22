# Context Intelligence Framework (CIF) - Chrome Extension (Manifest V3)

The CIF Chrome Extension brings real-time architectural context, drift detection, and historical decision insights directly into GitHub's web interface (Pull Request reviews and file browsing).

---

## 1. Installation (Unpacked Developer Mode)

1. Open Google Chrome (or any Chromium-based browser like Edge, Brave, or Arc).
2. Navigate to `chrome://extensions`.
3. In the top-right corner, toggle **Developer mode** to **ON**.
4. Click the **Load unpacked** button in the top-left corner.
5. Select the `extension/` folder in this repository:
   ```
   c:\Users\HP\Desktop\SE_project\extension
   ```
6. The extension **Context Intelligence Framework (CIF)** will appear in your installed extensions list.

> [!NOTE]
> The extension includes a stable development key in `manifest.json`. Under this key, its extension ID is:
> `pmkcmkalbgefpllgfmhgieeajolmefpi`
> If Chrome generates an ephemeral extension ID during your install, note the ID displayed on `chrome://extensions` for Step 2.

---

## 2. Backend & GitHub App Configuration

### A. Backend Allowed Origins (`.env`)
Add your extension ID to `CIF_EXTENSION_IDS` in your root `.env` file so the backend CORS policy permits cross-origin requests from the extension:
```bash
CIF_EXTENSION_IDS=pmkcmkalbgefpllgfmhgieeajolmefpi
```
Restart the backend server if running.

### B. GitHub App OAuth Settings
Ensure your GitHub App allows OAuth authentication for the extension:
1. Go to **GitHub Settings -> Developer Settings -> GitHub Apps -> [Your App]**.
2. Under **User authorization callback URL**, add:
   ```
   https://pmkcmkalbgefpllgfmhgieeajolmefpi.chromiumapp.org/
   ```
   *(Replace with your actual extension ID if different)*.

---

## 3. Extension Configuration (Options Page)

1. Right-click the CIF extension puzzle icon in the Chrome toolbar and select **Options** (or click the gear icon in the popup).
2. Configure your backend server URL:
   - Default: `http://127.0.0.1:8080` (Local Development)
   - Alternative: `http://localhost:8080`
3. Click **Save Configuration**. The extension validates the origin against an allowed security list before persisting to `chrome.storage.local`.

---

## 4. Key Workflows & Features

### A. Popup Authentication & Repository Status
- Click the CIF extension icon in the toolbar.
- **Signed Out**: Click **Sign in with GitHub**. Chrome opens `chrome.identity.launchWebAuthFlow`, redirects to GitHub OAuth, exchanges the code with the backend, and stores your secure JWT session.
- **Signed In**:
  - Displays your GitHub avatar and handle (`@username`).
  - Automatically identifies whether your current active tab is a GitHub repository.
  - Shows repository indexing status (Indexed, Ingestion Progress, or Unindexed).
  - Offers a **+ Add Repository to CIF** button for unindexed repositories.
  - Provides a quick link to **Open CIF Web Dashboard**.

### B. Pull Request Context & Drift Analysis
- Navigate to any GitHub Pull Request: `https://github.com/{owner}/{repo}/pull/{pr_number}`.
- CIF injects an isolated floating drawer in the bottom-right corner.
- Click the drawer handle to inspect:
  - **Drift Warnings**: Highlights if incoming diffs contradict past architectural decisions.
  - **Rejected Alternatives**: Warns if incoming code proposes approaches previously evaluated and rejected with rationale.
  - **Confidence Badges**: Displays high, medium, or low confidence scores.
  - **Interactive Feedback**: Click **Helpful** or **False Positive** to refine the backend scoring model.
  - **Head SHA Caching**: Background service worker caches analysis per commit SHA to minimize network overhead.

### C. Repository File Browsing & Active Decisions
- Navigate to any file in a repository: `https://github.com/{owner}/{repo}/blob/{branch}/{path}`.
- CIF drawer reveals:
  - **Active Decisions**: Architectural decisions governing this file and related components.
  - **Freshness Indicator**: Freshness badges indicating if decision context is current or needs re-evaluation.
  - **AST Function Links**: Targeted symbols and function references within the source file.

---

## 5. Security & Isolation Architecture

The CIF extension adheres to strict security principles:

1. **Rule R3 (Strict Isolation)**:
   - Private repository context is only returned to authenticated GitHub users with verified `read` or `admin` permissions.
   - Demo repositories remain globally accessible for review.
2. **Rule R4 (Token Confidentiality)**:
   - User JWT sessions are stored exclusively in `chrome.storage.local`.
   - Access tokens are never included in URL query parameters, page scripts, or browser console telemetry.
3. **Rule R5 (Zero `innerHTML`)**:
   - Zero `innerHTML`, `outerHTML`, or `insertAdjacentHTML` in the extension codebase.
   - All dynamic DOM nodes are constructed via standard `document.createElement`, `textContent`, and sanitizing DOM helpers (`el()`, `text()`, `safeUrl()`).
   - All links enforce `target="_blank"` and `rel="noopener noreferrer"`.
4. **Shadow-DOM Isolation**:
   - Floating widgets render inside an isolated `attachShadow({ mode: 'open' })` host element.
   - GitHub page styles cannot leak into or break CIF UI, and CIF styles cannot pollute GitHub page DOM.
5. **Turbo / SPA Navigation Resilience**:
   - Uses `MutationObserver` on `document.title` and GitHub's `turbo:visit` / `turbo:load` events to smoothly update context during client-side navigation without full page reloads.

---

## 6. Packaging & Building

To generate a clean production zip distribution:
```bash
python tools/build_extension.py
```
Output artifact:
```
dist/cif-extension.zip
```
*(Tests and development markdown files are automatically excluded).*

---

## 7. Automated Testing

Run the full extension test suite (Manifest V3 validation, GitHub URL parsing security, and Rule R5 AST/regex compliance):
```bash
python -m unittest extension/tests/test_manifest.py extension/tests/test_github_url.py extension/tests/test_security.py
```

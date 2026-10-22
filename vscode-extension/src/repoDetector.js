/**
 * CIF VS Code Extension - Repository Detector
 * Resolves GitHub {owner}/{repo} from workspace git configuration.
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

function parseGitRemoteUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== 'string') return null;
  const trimmed = rawUrl.trim();

  // Pattern 1: HTTPS (https://github.com/owner/repo.git or https://github.com/owner/repo)
  const httpsMatch = trimmed.match(/^https?:\/\/(?:[a-zA-Z0-9_\-\.]+@)?github\.com\/([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+?)(?:\.git)?$/i);
  if (httpsMatch) {
    return {
      owner: httpsMatch[1],
      repo: httpsMatch[2],
      fullName: `${httpsMatch[1]}/${httpsMatch[2]}`
    };
  }

  // Pattern 2: SSH (git@github.com:owner/repo.git)
  const sshMatch = trimmed.match(/^git@github\.com:([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+?)(?:\.git)?$/i);
  if (sshMatch) {
    return {
      owner: sshMatch[1],
      repo: sshMatch[2],
      fullName: `${sshMatch[1]}/${sshMatch[2]}`
    };
  }

  // Pattern 3: ssh://git@github.com/owner/repo.git
  const sshProtoMatch = trimmed.match(/^ssh:\/\/git@github\.com\/([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+?)(?:\.git)?$/i);
  if (sshProtoMatch) {
    return {
      owner: sshProtoMatch[1],
      repo: sshProtoMatch[2],
      fullName: `${sshProtoMatch[1]}/${sshProtoMatch[2]}`
    };
  }

  return null;
}

function detectRepoFromWorkspace(workspaceRoot) {
  if (!workspaceRoot) return null;

  // 1. Try running git remote get-url origin
  try {
    const stdout = execFileSync('git', ['remote', 'get-url', 'origin'], {
      cwd: workspaceRoot,
      encoding: 'utf-8',
      timeout: 3000
    });
    const parsed = parseGitRemoteUrl(stdout);
    if (parsed) return parsed;
  } catch (e) {
    // Fall back to reading .git/config manually
  }

  // 2. Fall back to parsing .git/config
  const gitConfigPath = path.join(workspaceRoot, '.git', 'config');
  if (fs.existsSync(gitConfigPath)) {
    try {
      const configText = fs.readFileSync(gitConfigPath, 'utf-8');
      const lines = configText.split(/\r?\n/);
      let inOriginSection = false;
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
          inOriginSection = trimmed === '[remote "origin"]';
          continue;
        }
        if (inOriginSection && trimmed.startsWith('url =')) {
          const rawUrl = trimmed.substring('url ='.length).trim();
          const parsed = parseGitRemoteUrl(rawUrl);
          if (parsed) return parsed;
        }
      }
    } catch (e) {
      // Ignore read errors
    }
  }

  return null;
}

module.exports = {
  parseGitRemoteUrl,
  detectRepoFromWorkspace
};

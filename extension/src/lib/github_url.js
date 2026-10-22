/**
 * Strict GitHub URL parser for CIF Chrome Extension (Step 8.6).
 * Safely parses GitHub location into repository, pull request, issue, and blob context.
 * Rejects enterprise lookalikes, non-github hosts, and non-repository paths.
 */

const RESERVED_TOP_PATHS = new Set([
  'about', 'pricing', 'features', 'enterprise', 'login', 'join', 'signup',
  'settings', 'notifications', 'explore', 'topics', 'trending', 'collections',
  'security', 'marketplace', 'issues', 'pulls', 'orgs', 'users', 'stars'
]);

export function parseGithubUrl(rawUrl) {
  const result = {
    valid: false,
    kind: 'unknown', // 'repo' | 'pull' | 'issue' | 'blob' | 'other'
    owner: null,
    repo: null,
    fullName: null,
    number: null,
    ref: null,
    path: null,
    line: null
  };

  if (!rawUrl) return result;

  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch (e) {
    return result;
  }

  // Host validation: must be exact github.com (or www.github.com)
  const host = parsed.hostname.toLowerCase();
  if (host !== 'github.com' && host !== 'www.github.com') {
    return result;
  }

  const segments = parsed.pathname.split('/').filter(Boolean);
  if (segments.length < 2) {
    return result;
  }

  const owner = segments[0];
  const repo = segments[1];

  if (RESERVED_TOP_PATHS.has(owner.toLowerCase())) {
    return result;
  }

  result.owner = owner;
  result.repo = repo;
  result.fullName = `${owner}/${repo}`;
  result.valid = true;

  if (segments.length === 2) {
    result.kind = 'repo';
    return result;
  }

  const subType = segments[2];

  // Pull request page: /owner/repo/pull/123[/files]
  if (subType === 'pull' && segments.length >= 4) {
    const num = parseInt(segments[3], 10);
    if (!isNaN(num) && num > 0) {
      result.kind = 'pull';
      result.number = num;
      return result;
    }
  }

  // Issue page: /owner/repo/issues/123
  if (subType === 'issues' && segments.length >= 4) {
    const num = parseInt(segments[3], 10);
    if (!isNaN(num) && num > 0) {
      result.kind = 'issue';
      result.number = num;
      return result;
    }
  }

  // Blob / File viewer: /owner/repo/blob/ref/path/to/file.py#L42
  if (subType === 'blob' && segments.length >= 5) {
    result.kind = 'blob';
    result.ref = segments[3];
    result.path = segments.slice(4).join('/');

    if (parsed.hash) {
      const lineMatch = parsed.hash.match(/^#L(\d+)/i);
      if (lineMatch) {
        result.line = parseInt(lineMatch[1], 10);
      }
    }
    return result;
  }

  // Tree / Directory: /owner/repo/tree/ref/path...
  if (subType === 'tree' && segments.length >= 4) {
    result.kind = 'tree';
    result.ref = segments[3];
    result.path = segments.slice(4).join('/') || '';
    return result;
  }

  result.kind = 'other';
  return result;
}

// CommonJS support for Node.js / Python runner tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { parseGithubUrl };
}

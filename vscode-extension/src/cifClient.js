/**
 * CIF VS Code Extension - API Client
 * Secure communication with CIF backend using VS Code SecretStorage.
 * Strict zero-token logging (Rule R4).
 */

const https = require('https');
const http = require('http');
const vscode = require('vscode');

const SECRET_KEY_TOKEN = 'cif_session_token';
const SECRET_KEY_USER = 'cif_user_login';

class CIFClient {
  /**
   * @param {vscode.ExtensionContext} context
   */
  constructor(context) {
    this.context = context;
  }

  getBaseUrl() {
    const config = vscode.workspace.getConfiguration('cif');
    const url = config.get('baseUrl') || 'http://127.0.0.1:8080';
    return url.replace(/\/+$/, '');
  }

  async getSessionToken() {
    return await this.context.secrets.get(SECRET_KEY_TOKEN);
  }

  async setSession(token, login) {
    await this.context.secrets.store(SECRET_KEY_TOKEN, token);
    if (login) {
      await this.context.secrets.store(SECRET_KEY_USER, login);
    }
  }

  async clearSession() {
    await this.context.secrets.delete(SECRET_KEY_TOKEN);
    await this.context.secrets.delete(SECRET_KEY_USER);
  }

  async getUserLogin() {
    return await this.context.secrets.get(SECRET_KEY_USER);
  }

  async _request(method, endpoint, body = null) {
    const baseUrl = this.getBaseUrl();
    const fullUrl = new URL(baseUrl + endpoint);
    const token = await this.getSessionToken();

    const headers = {
      'Accept': 'application/json',
      'User-Agent': 'CIF-VSCode/1.0.0'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (body) {
      headers['Content-Type'] = 'application/json';
    }

    const isHttps = fullUrl.protocol === 'https:';
    const clientLib = isHttps ? https : http;

    return new Promise((resolve, reject) => {
      const options = {
        hostname: fullUrl.hostname,
        port: fullUrl.port || (isHttps ? 443 : 80),
        path: fullUrl.pathname + fullUrl.search,
        method: method,
        headers: headers,
        timeout: 10000
      };

      const req = clientLib.request(options, (res) => {
        let rawData = '';
        res.on('data', (chunk) => { rawData += chunk; });
        res.on('end', () => {
          let parsed = null;
          try {
            parsed = rawData ? JSON.parse(rawData) : {};
          } catch (e) {
            parsed = { raw: rawData };
          }

          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve({ status: res.statusCode, data: parsed });
          } else {
            resolve({
              status: res.statusCode,
              error: parsed.message || parsed.error || `HTTP ${res.statusCode}`,
              data: parsed
            });
          }
        });
      });

      req.on('error', (err) => {
        reject(new Error(`Failed to connect to CIF backend: ${err.message}`));
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('CIF backend request timed out'));
      });

      if (body) {
        req.write(JSON.stringify(body));
      }
      req.end();
    });
  }

  async exchangeCode(code) {
    const res = await this._request('POST', '/auth/token/exchange', { code });
    if (res.status === 200 && res.data && res.data.token) {
      await this.setSession(res.data.token, res.data.login || 'User');
      return res.data;
    }
    throw new Error(res.error || 'Token exchange failed');
  }

  async getCurrentUser() {
    return await this._request('GET', '/api/me');
  }

  async getFileContext(repo, path) {
    const params = new URLSearchParams({ repo, path });
    return await this._request('GET', `/api/file-context?${params.toString()}`);
  }

  async getRepoStatus(repo) {
    const params = new URLSearchParams({ repo });
    return await this._request('GET', `/api/repos/status?${params.toString()}`);
  }

  async addRepository(repo) {
    return await this._request('POST', '/api/repos', { repo });
  }

  async getDecisions(repo) {
    const params = new URLSearchParams({ repo });
    return await this._request('GET', `/api/decisions?${params.toString()}`);
  }

  async evaluateGuardRules(repo, files) {
    return await this._request('POST', '/api/guard-rules/evaluate', { repo, files });
  }
}

module.exports = {
  CIFClient,
  SECRET_KEY_TOKEN,
  SECRET_KEY_USER
};

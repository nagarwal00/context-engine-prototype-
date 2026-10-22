/**
 * CIF VS Code Extension - Symbol Extractor
 * Identifies functions, methods, and classes to bind architectural CodeLenses.
 */

const vscode = require('vscode');

function extractSymbols(document) {
  const symbols = [];
  const text = document.getText();
  const lines = text.split(/\r?\n/);

  // Common pattern matchers per language
  const patterns = [
    // Python functions & classes
    /^\s*(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(/,
    /^\s*class\s+([a-zA-Z0-9_]+)\s*[:\(]/,
    // JS/TS functions & classes
    /^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(/,
    /^\s*(?:export\s+)?class\s+([a-zA-Z0-9_]+)/,
    /^\s*(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>/,
    // Go functions & methods
    /^\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)\s*\(/,
    // Rust functions
    /^\s*(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)\s*\(/
  ];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const pat of patterns) {
      const match = line.match(pat);
      if (match) {
        const symbolName = match[1];
        const range = new vscode.Range(i, 0, i, line.length);
        symbols.push({
          name: symbolName,
          line: i + 1, // 1-indexed for display
          range: range
        });
        break; // Match first pattern for this line
      }
    }
  }

  return symbols;
}

module.exports = {
  extractSymbols
};

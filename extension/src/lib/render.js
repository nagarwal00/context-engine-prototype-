/**
 * Safe DOM rendering utilities for CIF Chrome Extension (Step 8.7).
 * Rule R5: Absolute zero innerHTML / outerHTML / insertAdjacentHTML.
 * All text injected exclusively via textContent or TextNodes.
 * All URLs sanitized with safeUrl (http/https only) with rel="noopener noreferrer".
 */

export function safeUrl(url) {
  if (!url) return '#';
  const str = String(url).trim();
  if (/^https?:\/\//i.test(str)) {
    return str;
  }
  return '#';
}

export function el(tag, attrs = {}, children = []) {
  const element = document.createElement(tag);

  for (const [key, val] of Object.entries(attrs)) {
    if (val === null || val === undefined) continue;
    if (key === 'className' || key === 'class') {
      element.className = String(val);
    } else if (key === 'style' && typeof val === 'object') {
      Object.assign(element.style, val);
    } else if (key.startsWith('on') && typeof val === 'function') {
      const eventName = key.slice(2).toLowerCase();
      element.addEventListener(eventName, val);
    } else if (key === 'href') {
      element.setAttribute('href', safeUrl(val));
      element.setAttribute('target', '_blank');
      element.setAttribute('rel', 'noopener noreferrer');
    } else if (key.startsWith('data-')) {
      element.setAttribute(key, String(val));
    } else {
      element.setAttribute(key, String(val));
    }
  }

  const childList = Array.isArray(children) ? children : [children];
  for (const child of childList) {
    if (child === null || child === undefined) continue;
    if (typeof child === 'string' || typeof child === 'number') {
      element.appendChild(document.createTextNode(String(child)));
    } else if (child instanceof Node) {
      element.appendChild(child);
    }
  }

  return element;
}

export function text(content) {
  return document.createTextNode(String(content ?? ''));
}

export function createBadge(label, type = 'info') {
  return el('span', { className: `cif-badge cif-badge-${type}` }, [text(label)]);
}

export function createButton(label, className = 'cif-btn-secondary', onClick = null) {
  return el('button', {
    type: 'button',
    className: `cif-btn ${className}`,
    onClick: onClick
  }, [text(label)]);
}

// CommonJS support for Node.js / Python runner tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { safeUrl, el, text, createBadge, createButton };
}

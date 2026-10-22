/**
 * Message protocol constants and schema validators for CIF Extension (Step 8.7).
 * Rule R7: Enforces strict message types and payload shapes between content script and background.
 */

export const MessageTypes = {
  GET_AUTH_STATUS: 'CIF_GET_AUTH_STATUS',
  SIGN_IN: 'CIF_SIGN_IN',
  SIGN_OUT: 'CIF_SIGN_OUT',
  GET_REPO_STATUS: 'CIF_GET_REPO_STATUS',
  ADD_REPO: 'CIF_ADD_REPO',
  GET_PR_ANALYSIS: 'CIF_GET_PR_ANALYSIS',
  GET_FILE_CONTEXT: 'CIF_GET_FILE_CONTEXT',
  SEND_FEEDBACK: 'CIF_SEND_FEEDBACK',
  GET_CONFIG: 'CIF_GET_CONFIG',
  SET_CONFIG: 'CIF_SET_CONFIG'
};

export const ALLOWED_MESSAGE_TYPES = new Set(Object.values(MessageTypes));

export function validateMessage(msg) {
  if (!msg || typeof msg !== 'object') {
    return { valid: false, error: 'Message must be an object' };
  }
  if (!ALLOWED_MESSAGE_TYPES.has(msg.type)) {
    return { valid: false, error: `Disallowed message type: ${msg.type}` };
  }
  return { valid: true };
}

// CommonJS support for Node.js / Python runner tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MessageTypes, ALLOWED_MESSAGE_TYPES, validateMessage };
}

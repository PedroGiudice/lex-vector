/**
 * Development token generator for claudecodeui backend
 *
 * WARNING: This uses a known dev secret and should NEVER be used in production.
 * The secret is hardcoded in the claudecodeui backend for development purposes.
 */

// Simple base64url encoding (no external dependencies)
function base64urlEncode(str: string): string {
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

// HMAC-SHA256 implementation using Web Crypto API
async function hmacSHA256(key: string, message: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(key);
  const messageData = encoder.encode(message);

  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageData);
  const signatureArray = new Uint8Array(signature);

  // Convert to base64url
  let binary = '';
  for (let i = 0; i < signatureArray.length; i++) {
    binary += String.fromCharCode(signatureArray[i]);
  }
  return base64urlEncode(binary);
}

/**
 * Generates a development JWT token for claudecodeui backend
 * Uses the default dev secret from the backend
 */
export async function generateDevToken(): Promise<string> {
  // DEV SECRET - same as claudecodeui backend default
  const DEV_SECRET = 'claude-ui-dev-secret-change-in-production';

  const header = {
    alg: 'HS256',
    typ: 'JWT',
  };

  const payload = {
    userId: 1,
    username: 'dev-user',
    iat: Math.floor(Date.now() / 1000),
  };

  const headerEncoded = base64urlEncode(JSON.stringify(header));
  const payloadEncoded = base64urlEncode(JSON.stringify(payload));
  const message = `${headerEncoded}.${payloadEncoded}`;

  const signature = await hmacSHA256(DEV_SECRET, message);

  return `${message}.${signature}`;
}

/**
 * Sets the JWT cookie for WebSocket authentication
 */
export async function setDevAuthCookie(): Promise<string> {
  const token = await generateDevToken();
  document.cookie = `jwt=${token}; path=/; SameSite=Lax`;
  return token;
}

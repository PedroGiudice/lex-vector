/**
 * Chat utility functions
 */

/**
 * Decode HTML entities in text
 */
export function decodeHtmlEntities(text) {
  if (!text) return text;
  return text
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&');
}

/**
 * Normalize markdown text where providers mistakenly wrap short inline code with single-line triple fences.
 */
export function normalizeInlineCodeFences(text) {
  if (!text || typeof text !== 'string') return text;
  try {
    return text.replace(/```\s*([^\n\r]+?)\s*```/g, '`$1`');
  } catch {
    return text;
  }
}

/**
 * Unescape \n, \t, \r while protecting LaTeX formulas
 */
export function unescapeWithMathProtection(text) {
  if (!text || typeof text !== 'string') return text;

  const mathBlocks = [];
  const PLACEHOLDER_PREFIX = '__MATH_BLOCK_';
  const PLACEHOLDER_SUFFIX = '__';

  // Extract and protect math formulas
  let processedText = text.replace(/\$\$([\s\S]*?)\$\$|\$([^\$\n]+?)\$/g, (match) => {
    const index = mathBlocks.length;
    mathBlocks.push(match);
    return `${PLACEHOLDER_PREFIX}${index}${PLACEHOLDER_SUFFIX}`;
  });

  // Process escape sequences
  processedText = processedText
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '\r');

  // Restore math formulas
  processedText = processedText.replace(
    new RegExp(`${PLACEHOLDER_PREFIX}(\\d+)${PLACEHOLDER_SUFFIX}`, 'g'),
    (match, index) => mathBlocks[parseInt(index)]
  );

  return processedText;
}

/**
 * Format usage limit text with local timezone
 */
export function formatUsageLimitText(text) {
  try {
    if (typeof text !== 'string') return text;
    return text.replace(/Claude AI usage limit reached\|(\d{10,13})/g, (match, ts) => {
      let timestampMs = parseInt(ts, 10);
      if (!Number.isFinite(timestampMs)) return match;
      if (timestampMs < 1e12) timestampMs *= 1000;

      const reset = new Date(timestampMs);
      const timeStr = new Intl.DateTimeFormat(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }).format(reset);

      const offsetMinutesLocal = -reset.getTimezoneOffset();
      const sign = offsetMinutesLocal >= 0 ? '+' : '-';
      const abs = Math.abs(offsetMinutesLocal);
      const offH = Math.floor(abs / 60);
      const offM = abs % 60;
      const gmt = `GMT${sign}${offH}${offM ? ':' + String(offM).padStart(2, '0') : ''}`;

      const tzId = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
      const cityRaw = tzId.split('/').pop() || '';
      const city = cityRaw.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
      const tzHuman = city ? `${gmt} (${city})` : gmt;

      const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const dateReadable = `${reset.getDate()} ${months[reset.getMonth()]} ${reset.getFullYear()}`;

      return `Claude usage limit reached. Your limit will reset at **${timeStr} ${tzHuman}** - ${dateReadable}`;
    });
  } catch {
    return text;
  }
}

/**
 * Safe localStorage wrapper to handle quota exceeded errors
 */
export const safeLocalStorage = {
  setItem: (key, value) => {
    try {
      if (key.startsWith('chat_messages_') && typeof value === 'string') {
        try {
          const parsed = JSON.parse(value);
          if (Array.isArray(parsed) && parsed.length > 50) {
            console.warn(`Truncating chat history for ${key}`);
            value = JSON.stringify(parsed.slice(-50));
          }
        } catch {}
      }
      localStorage.setItem(key, value);
    } catch (error) {
      if (error.name === 'QuotaExceededError') {
        console.warn('localStorage quota exceeded, clearing old data');
        const keys = Object.keys(localStorage);
        const chatKeys = keys.filter(k => k.startsWith('chat_messages_')).sort();
        if (chatKeys.length > 3) {
          chatKeys.slice(0, chatKeys.length - 3).forEach(k => localStorage.removeItem(k));
        }
        try {
          localStorage.setItem(key, value);
        } catch {}
      }
    }
  },
  getItem: (key) => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  removeItem: (key) => {
    try {
      localStorage.removeItem(key);
    } catch {}
  }
};

// color-palette-v2.js - Professional ANSI 256 color palette
//
// Design by frontend-design skill (Fase 1.5)
// Implements dark, cohesive terminal UI with subtle backgrounds
//
// USAGE RULES:
// - bg_primary: Main background for Line 1
// - bg_secondary: Secondary background for Line 2
// - bg_accent: Accent background for Line 3 (coaching)
// - fg_primary: Main text (high contrast)
// - fg_secondary: Secondary text (medium contrast)
// - fg_tertiary: Subtle elements (separators, hints)
// - success/warning/error/info: Semantic colors
// - accent_purple: VibbinLoggin branding
// - gordon: Gordon Ramsay coaching accent

const PALETTE = {
  // Background colors (subtle, dark)
  bg_primary:   '\x1b[48;5;234m', // #1c1c1c - darkest
  bg_secondary: '\x1b[48;5;235m', // #262626 - medium dark
  bg_accent:    '\x1b[48;5;236m', // #303030 - lighter dark (coaching)

  // Foreground colors (text)
  fg_primary:   '\x1b[38;5;254m', // #e4e4e4 - bright white (main text)
  fg_secondary: '\x1b[38;5;245m', // #8a8a8a - medium gray (labels)
  fg_tertiary:  '\x1b[38;5;240m', // #585858 - dark gray (separators)

  // Semantic colors (state indicators)
  success:      '\x1b[38;5;114m', // #87d787 - soft green
  warning:      '\x1b[38;5;221m', // #ffd75f - soft yellow
  error:        '\x1b[38;5;204m', // #ff5f87 - coral red
  info:         '\x1b[38;5;117m', // #87d7ff - sky blue

  // Accent colors (branding)
  accent_purple:'\x1b[38;5;141m', // #af87ff - VibbinLoggin purple
  gordon:       '\x1b[38;5;208m', // #ff8700 - Gordon Ramsay orange

  // Utility codes
  reset:        '\x1b[0m',
  bold:         '\x1b[1m',
  dim:          '\x1b[2m'
};

/**
 * Apply foreground color to text with auto-reset
 * @param {string} text - Text to colorize
 * @param {string} colorName - Color name from PALETTE (e.g., 'success', 'fg_primary')
 * @returns {string} - Colorized text with reset code
 */
function colorize(text, colorName) {
  if (!PALETTE[colorName]) {
    // Fallback: return text as-is if color doesn't exist
    return text;
  }
  return PALETTE[colorName] + text + PALETTE.reset;
}

/**
 * Apply background color (use for full lines)
 * @param {string} bgName - Background color name (e.g., 'bg_primary')
 * @returns {string} - ANSI code for background (no reset - must be applied manually)
 */
function bg(bgName) {
  return PALETTE[bgName] || '';
}

/**
 * Clear all formatting and return to default
 * @returns {string} - Reset code
 */
function reset() {
  return PALETTE.reset;
}

/**
 * Create separator with tertiary color
 * @param {string} char - Character to use (default: '╌')
 * @param {number} count - How many times to repeat
 * @returns {string} - Colored separator
 */
function separator(char = '╌', count = 1) {
  return colorize(char.repeat(count), 'fg_tertiary');
}

/**
 * Strip ANSI codes from string (useful for length calculation)
 * @param {string} str - String with ANSI codes
 * @returns {string} - Clean string without ANSI
 */
function stripAnsi(str) {
  return str.replace(/\x1b\[[0-9;]*m/g, '');
}

/**
 * Get visible length of string (excluding ANSI codes)
 * @param {string} str - String to measure
 * @returns {number} - Visible character count
 */
function visibleLength(str) {
  return stripAnsi(str).length;
}

module.exports = {
  PALETTE,
  colorize,
  bg,
  reset,
  separator,
  stripAnsi,
  visibleLength
};

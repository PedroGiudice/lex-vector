// color-palette.js - Paleta de cores vibrante e coesa para statusline
//
// REGRAS DE USO:
// - Cyan: Git, venv, contexto de ambiente
// - Green: Success states, checks ✓
// - Blue (claro): Skills, agents, tools
// - Purple: VibbinLoggin, analytics, metrics
// - Yellow: Warnings (uso moderado)
// - Red (coral): Errors only
// - Gray: Separadores │

// ANSI 256-color codes (bright variants)
const colors = {
  // Principais (vibrantes)
  cyan: '\x1b[38;5;51m',      // #00FFFF (bright cyan)
  green: '\x1b[38;5;48m',     // #00FF87 (spring green)
  blue: '\x1b[38;5;75m',      // #5FAFFF (sky blue - CLARO)
  purple: '\x1b[38;5;141m',   // #AF87FF (medium purple)

  // Secundárias
  yellow: '\x1b[38;5;227m',   // #FFFF5F (light yellow - warnings)

  // Neutras
  gray: '\x1b[38;5;245m',     // #8A8A8A (separadores)
  white: '\x1b[38;5;15m',     // #FFFFFF (texto principal)

  // Especiais
  red: '\x1b[38;5;203m',      // #FF5F5F (coral red - APENAS erros)

  // Utilitários
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m'
};

// Helper para aplicar cor + reset automático
function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

// Helper para separador (sempre gray)
function separator() {
  return colorize('│', 'gray');
}

module.exports = {
  colors,
  colorize,
  separator
};

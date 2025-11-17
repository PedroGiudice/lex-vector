// cli-spinner.js - Spinner clássico de CLI (dots)
//
// Design: Spinner de pontos rotativo padrão usado em terminais
// - 10 frames para rotação suave
// - 80ms interval = velocidade padrão de CLI

const fs = require('fs');
const path = require('path');

// Spinner frames: dots rotativo clássico
const cliSpinner = {
  frames: [
    '⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'
  ],
  interval: 80,  // Velocidade padrão de CLI
};

// Estado do spinner (persiste entre chamadas)
let currentFrame = 0;
let lastUpdate = 0;

// Arquivo de estado (para sincronização entre hooks)
const STATE_FILE = path.join(process.env.HOME || '/home/cmr-auto', '.claude/statusline/spinner-state.json');

// Inicializar estado
function initState() {
  try {
    const stateDir = path.dirname(STATE_FILE);
    if (!fs.existsSync(stateDir)) {
      fs.mkdirSync(stateDir, { recursive: true });
    }

    if (fs.existsSync(STATE_FILE)) {
      const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
      currentFrame = state.frame || 0;
      lastUpdate = state.timestamp || 0;
    }
  } catch (err) {
    // Silenciar erros - usar estado padrão
  }
}

// Salvar estado
function saveState() {
  try {
    fs.writeFileSync(STATE_FILE, JSON.stringify({
      frame: currentFrame,
      timestamp: Date.now()
    }));
  } catch (err) {
    // Silenciar erros
  }
}

// Obter frame atual do spinner
function getCurrentFrame() {
  initState();

  const now = Date.now();
  const elapsed = now - lastUpdate;

  // Avançar frame se passou tempo suficiente
  if (elapsed >= cliSpinner.interval) {
    currentFrame = (currentFrame + 1) % cliSpinner.frames.length;
    lastUpdate = now;
    saveState();
  }

  return cliSpinner.frames[currentFrame];
}

// Resetar spinner (útil para testes)
function reset() {
  currentFrame = 0;
  lastUpdate = 0;
  saveState();
}

module.exports = {
  frames: cliSpinner.frames,
  interval: cliSpinner.interval,
  getCurrentFrame,
  reset
};

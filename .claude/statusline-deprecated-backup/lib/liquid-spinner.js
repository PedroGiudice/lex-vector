// liquid-spinner.js - Spinner viscoso com transparência e movimento irregular
//
// Design: "Líquido espesso" que se move de forma não-circular
// - Fade in/out (transparente → sólido → transparente)
// - Movimento assimétrico (não gira em eixo fixo)
// - 24 frames para movimento suave mas imprevisível
// - 130ms interval = ritmo "espesso"

const fs = require('fs');
const path = require('path');

// Spinner frames: transparente → sólido → transparente
const liquidSpinner = {
  frames: [
    // Fase 1: Emergindo (transparente → semi-sólido)
    '⋅  ', '◦⠁ ', '○⠂ ', '◌⠄ ',
    '◐⡀ ', '◓⢀ ',                 // Solidificando

    // Fase 2: Morfando (movimento assimétrico)
    '◑⠠ ', '◒⠐ ', '◴⠈ ', '◷⠁ ',
    '◶⠂ ', '◵⠄ ',

    // Fase 3: Densificando (braille + blocos)
    '⠋░ ', '⠙▒ ', '⠹▓ ',         // Espessando

    // Fase 4: Diluindo (sólido → transparente)
    '⠸▒ ', '⠼░ ', '⠴⋅ ',
    '⠦◦ ', '⠧○ ',                 // Transparência aumentando

    // Fase 5: Reset suave
    '⡇◌ ', '⠏· ', '⠋⋅ ', '⠁  '   // Fade out
  ],
  interval: 130,  // Ritmo lento = "espesso"
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
  if (elapsed >= liquidSpinner.interval) {
    currentFrame = (currentFrame + 1) % liquidSpinner.frames.length;
    lastUpdate = now;
    saveState();
  }

  return liquidSpinner.frames[currentFrame];
}

// Resetar spinner (útil para testes)
function reset() {
  currentFrame = 0;
  lastUpdate = 0;
  saveState();
}

module.exports = {
  frames: liquidSpinner.frames,
  interval: liquidSpinner.interval,
  getCurrentFrame,
  reset
};

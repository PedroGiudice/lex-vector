// last-used-tracker.js - Rastreia última execução de hooks, agentes e skills
const fs = require('fs');
const path = require('path');

const TRACKER_FILE = path.join(
  process.env.HOME || '/home/cmr-auto',
  '.claude/statusline/last-used.json'
);

// Inicializar arquivo de tracking
function initTracker() {
  try {
    const dir = path.dirname(TRACKER_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    if (!fs.existsSync(TRACKER_FILE)) {
      fs.writeFileSync(TRACKER_FILE, JSON.stringify({
        hooks: {},
        agents: {},
        skills: {},
        orchestrator: null
      }, null, 2));
    }
  } catch (err) {
    // Silenciar erros
  }
}

// Ler dados de tracking
function readTracker() {
  initTracker();
  try {
    const data = fs.readFileSync(TRACKER_FILE, 'utf8');
    return JSON.parse(data);
  } catch (err) {
    return { hooks: {}, agents: {}, skills: {}, orchestrator: null };
  }
}

// Salvar dados de tracking
function saveTracker(data) {
  try {
    fs.writeFileSync(TRACKER_FILE, JSON.stringify(data, null, 2));
  } catch (err) {
    // Silenciar erros
  }
}

// Atualizar última execução de um hook
function updateHook(hookName) {
  const tracker = readTracker();
  tracker.hooks[hookName] = Date.now();
  saveTracker(tracker);
}

// Atualizar última execução de um agente
function updateAgent(agentName) {
  const tracker = readTracker();
  tracker.agents[agentName] = Date.now();
  saveTracker(tracker);
}

// Atualizar última execução de uma skill
function updateSkill(skillName) {
  const tracker = readTracker();
  tracker.skills[skillName] = Date.now();
  saveTracker(tracker);
}

// Atualizar última execução do orchestrator
function updateOrchestrator() {
  const tracker = readTracker();
  tracker.orchestrator = Date.now();
  saveTracker(tracker);
}

// Obter última execução (retorna string formatada)
function getLastUsed(timestamp) {
  if (!timestamp) return 'never';

  const now = Date.now();
  const diff = now - timestamp;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return `${seconds}s ago`;
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

// Obter todos os dados formatados
function getAllLastUsed() {
  const tracker = readTracker();

  return {
    hooks: Object.fromEntries(
      Object.entries(tracker.hooks).map(([name, ts]) => [name, getLastUsed(ts)])
    ),
    agents: Object.fromEntries(
      Object.entries(tracker.agents).map(([name, ts]) => [name, getLastUsed(ts)])
    ),
    skills: Object.fromEntries(
      Object.entries(tracker.skills).map(([name, ts]) => [name, getLastUsed(ts)])
    ),
    orchestrator: getLastUsed(tracker.orchestrator)
  };
}

module.exports = {
  updateHook,
  updateAgent,
  updateSkill,
  updateOrchestrator,
  getLastUsed,
  getAllLastUsed,
  readTracker
};

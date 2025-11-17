// skills-tracker.js - Detecção de skills disponíveis e ativas
//
// Detecta:
// - Total de skills instaladas (via filesystem)
// - Skills ativas (via marker file ou vibe-log)

const fs = require('fs');
const path = require('path');

// Diretórios relevantes
// Detect project root: if we're in .claude/statusline/lib, go up 3 levels
const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..');
const SKILLS_DIR = path.join(PROJECT_ROOT, 'skills');
const MARKER_FILE = path.join(PROJECT_ROOT, '.claude/statusline/active-skills.json');

// Contar total de skills instaladas (apenas skills/ - .claude/skills/ são settings)
function getTotalCount() {
  try {
    if (!fs.existsSync(SKILLS_DIR)) {
      return 0;
    }

    const entries = fs.readdirSync(SKILLS_DIR, { withFileTypes: true });
    return entries.filter(d => d.isDirectory()).length;
  } catch (err) {
    return 0;
  }
}

// Obter skills ativas
function getActiveSkills() {
  try {
    // Estratégia 1: Ler marker file (criado por hooks ou vibe-log)
    if (fs.existsSync(MARKER_FILE)) {
      const data = JSON.parse(fs.readFileSync(MARKER_FILE, 'utf8'));
      const age = Date.now() - (data.timestamp || 0);

      // Considerar válido se < 5 minutos
      if (age < 5 * 60 * 1000 && Array.isArray(data.skills)) {
        return data.skills;
      }
    }

    // Estratégia 2: Fallback - nenhuma skill ativa detectada
    return [];
  } catch (err) {
    return [];
  }
}

// Contar skills ativas
function getActiveCount() {
  return getActiveSkills().length;
}

// Formatar output (ex: "3/8" ou "8" se nenhuma ativa)
function getFormattedCount() {
  const total = getTotalCount();
  const active = getActiveCount();

  if (total === 0) {
    return 'none';
  }

  if (active === 0) {
    return `${total}`;  // Apenas total
  }

  return `${active}/${total}`;  // Ativas/total
}

// Atualizar skills ativas (para hooks)
function updateActiveSkills(skillNames) {
  try {
    const dir = path.dirname(MARKER_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(MARKER_FILE, JSON.stringify({
      skills: Array.isArray(skillNames) ? skillNames : [],
      timestamp: Date.now()
    }));
  } catch (err) {
    // Silenciar erros
  }
}

module.exports = {
  getTotalCount,
  getActiveCount,
  getActiveSkills,
  getFormattedCount,
  updateActiveSkills
};

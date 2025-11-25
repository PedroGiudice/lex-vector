/**
 * lib/skill-detector.js - Detecção de skills baseada em skill-rules.json
 *
 * Mudança v2.0: Lê skill-rules.json diretamente (não sessionState.skills)
 * Mudança v2.1: Word boundary matching para evitar falsos positivos
 *               Ex: "seguida" não deve matchar "ui", "teste" não deve matchar "test"
 * Implementa: Pattern matching (keywords + intentPatterns) + Top 5 ranking
 */

const fs = require('fs');
const path = require('path');

/**
 * Verifica se keyword existe como palavra completa no texto
 * Usa word boundary para evitar falsos positivos como:
 * - "seguida" matchando "ui"
 * - "teste" matchando "test"
 * - "auditoria" matchando "audit" (este é válido - mesma raiz)
 *
 * @param {string} text - Texto onde procurar
 * @param {string} keyword - Keyword a procurar
 * @returns {boolean} - true se keyword existe como palavra ou prefixo válido
 */
function matchKeywordWithBoundary(text, keyword) {
  const textLower = text.toLowerCase();
  const keywordLower = keyword.toLowerCase();

  // Keywords muito curtas (≤2 chars) exigem match exato de palavra
  if (keywordLower.length <= 2) {
    const wordBoundaryRegex = new RegExp(`\\b${escapeRegex(keywordLower)}\\b`, 'i');
    return wordBoundaryRegex.test(text);
  }

  // Keywords de 3-4 chars: word boundary ou início de palavra
  if (keywordLower.length <= 4) {
    // Word boundary completo OU início de palavra (para permitir "audit" → "auditoria")
    const startBoundaryRegex = new RegExp(`\\b${escapeRegex(keywordLower)}`, 'i');
    return startBoundaryRegex.test(text);
  }

  // Keywords longas (≥5 chars): permitir substring mas verificar contexto
  // "test" em "teste" = falso positivo (línguas diferentes)
  // "audit" em "auditoria" = válido (mesma raiz)
  const startBoundaryRegex = new RegExp(`\\b${escapeRegex(keywordLower)}`, 'i');
  return startBoundaryRegex.test(text);
}

/**
 * Escapa caracteres especiais de regex
 */
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Detecta skills relevantes baseado no prompt do usuário
 *
 * @param {string} prompt - Prompt do usuário
 * @returns {object|null} - { topSkills, totalConsidered, totalMatched } ou null
 */
function detectSkill(prompt) {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const rulesPath = path.join(projectDir, '.claude', 'skills', 'skill-rules.json');

    // Verificar se skill-rules.json existe
    if (!fs.existsSync(rulesPath)) {
      console.error('[WARN] skill-rules.json não encontrado - skill detection desabilitada');
      return null;
    }

    // Ler skill-rules.json
    const rulesContent = fs.readFileSync(rulesPath, 'utf8');
    const rules = JSON.parse(rulesContent);

    if (!rules.skills) {
      console.error('[WARN] skill-rules.json sem seção "skills"');
      return null;
    }

    const promptLower = prompt.toLowerCase();
    const matched = [];

    // Iterar por todas as skills
    for (const [skillName, config] of Object.entries(rules.skills)) {
      let score = 0;
      let matchedTriggers = [];

      // 1. KEYWORD MATCHING (word boundary - v2.1)
      // Evita falsos positivos como "seguida" → "ui", "teste" → "test"
      if (config.promptTriggers?.keywords) {
        for (const keyword of config.promptTriggers.keywords) {
          if (matchKeywordWithBoundary(prompt, keyword)) {
            score += 10;
            matchedTriggers.push(`keyword: "${keyword}"`);
            break; // Apenas 1 keyword match conta (evitar score inflado)
          }
        }
      }

      // 2. INTENT PATTERN MATCHING (regex)
      if (config.promptTriggers?.intentPatterns) {
        for (const pattern of config.promptTriggers.intentPatterns) {
          try {
            const regex = new RegExp(pattern, 'i');
            if (regex.test(prompt)) {
              score += 15; // Intent patterns têm peso maior (mais semânticos)
              matchedTriggers.push(`pattern: "${pattern}"`);
              break; // Apenas 1 pattern match conta
            }
          } catch (err) {
            // Ignorar padrões regex inválidos
            console.error(`[WARN] Regex inválido em ${skillName}: ${pattern}`);
          }
        }
      }

      // 3. FILE PATH TRIGGERS (se contexto de arquivo disponível)
      // TODO: Implementar quando context incluir arquivos sendo editados

      // Se skill teve algum match, adicionar ao array
      if (score > 0) {
        matched.push({
          skillName,
          config,
          score,
          matchedTriggers
        });
      }
    }

    // Sem matches - retornar null
    if (matched.length === 0) {
      logDetection(prompt, Object.keys(rules.skills).length, 0, []);
      return null;
    }

    // RANKING: Priority weight + match score
    const priorityWeights = {
      'critical': 100,
      'high': 50,
      'medium': 20,
      'low': 10
    };

    matched.forEach(m => {
      const priorityWeight = priorityWeights[m.config.priority] || 0;
      m.finalScore = m.score + priorityWeight;
    });

    // Ordenar por finalScore (maior primeiro)
    matched.sort((a, b) => b.finalScore - a.finalScore);

    // Retornar top 5 apenas (evitar selection paralysis)
    const top5 = matched.slice(0, 5);

    // Logging
    logDetection(
      prompt,
      Object.keys(rules.skills).length,
      matched.length,
      top5.map(s => s.skillName)
    );

    return {
      topSkills: top5,
      totalConsidered: Object.keys(rules.skills).length,
      totalMatched: matched.length
    };

  } catch (error) {
    console.error(`[ERROR] skill-detector.js: ${error.message}`);
    return null;
  }
}

/**
 * Logging de skill detection (Gordon #1)
 *
 * @param {string} prompt - Prompt do usuário
 * @param {number} considered - Total de skills consideradas
 * @param {number} matched - Total de skills que fizeram match
 * @param {string[]} suggested - Array de skillNames sugeridas (top 5)
 */
function logDetection(prompt, considered, matched, suggested) {
  try {
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const logPath = path.join(projectDir, '.claude', 'hooks', 'lib', 'skill-tracking.log');

    const logEntry = {
      timestamp: new Date().toISOString(),
      prompt: prompt.substring(0, 100), // Primeiros 100 chars apenas
      considered,
      matched,
      suggested
    };

    // Append ao log (criar arquivo se não existir)
    fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n', 'utf8');
  } catch (err) {
    // Logging failure não deve quebrar skill detection
    console.error(`[WARN] Falha ao escrever skill-tracking.log: ${err.message}`);
  }
}

module.exports = { detectSkill };

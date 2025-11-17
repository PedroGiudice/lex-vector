// mcp-monitor.js - Monitor de MCP (Model Context Protocol) servers
//
// Detecta MCP servers configurados e seu status

const fs = require('fs');
const path = require('path');

// Possíveis locais de configuração MCP
const MCP_CONFIG_PATHS = [
  path.join(process.env.HOME || '/home/cmr-auto', '.claude/mcp.json'),
  path.join(process.env.HOME || '/home/cmr-auto', '.config/claude/mcp.json'),
  path.join(process.cwd(), '.claude/mcp.json')
];

// Verificar se MCP está configurado
function isAvailable() {
  return MCP_CONFIG_PATHS.some(p => fs.existsSync(p));
}

// Obter configuração MCP
function getConfig() {
  for (const configPath of MCP_CONFIG_PATHS) {
    try {
      if (fs.existsSync(configPath)) {
        const content = fs.readFileSync(configPath, 'utf8');
        return JSON.parse(content);
      }
    } catch (err) {
      // Continuar tentando outros caminhos
    }
  }
  return null;
}

// Listar servers configurados
function getServers() {
  const config = getConfig();
  if (!config || !config.mcpServers) {
    return [];
  }

  return Object.keys(config.mcpServers);
}

// Contar servers
function getServerCount() {
  return getServers().length;
}

// Health check básico (verifica se comando existe)
function checkServerHealth(serverName) {
  const config = getConfig();
  if (!config || !config.mcpServers || !config.mcpServers[serverName]) {
    return false;
  }

  const server = config.mcpServers[serverName];

  // Se tem comando, verificar se executável existe
  if (server.command) {
    try {
      const { execSync } = require('child_process');
      execSync(`which ${server.command}`, { stdio: 'ignore', timeout: 100 });
      return true;
    } catch {
      return false;
    }
  }

  // Se não tem comando definido, assumir que está OK
  return true;
}

// Obter status de todos os servers
function getServerStatuses() {
  const servers = getServers();
  const statuses = {};

  for (const server of servers) {
    statuses[server] = checkServerHealth(server);
  }

  return statuses;
}

// Formatar status para exibição
function getFormattedStatus() {
  if (!isAvailable()) {
    return null;
  }

  const servers = getServers();
  if (servers.length === 0) {
    return null;
  }

  const statuses = getServerStatuses();
  const healthy = Object.values(statuses).filter(Boolean).length;
  const total = servers.length;

  if (healthy === total) {
    return `${total} server${total > 1 ? 's' : ''} ✓`;
  } else {
    return `${healthy}/${total} servers`;
  }
}

module.exports = {
  isAvailable,
  getConfig,
  getServers,
  getServerCount,
  checkServerHealth,
  getServerStatuses,
  getFormattedStatus
};

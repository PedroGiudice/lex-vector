# JURI - Jurisprudência CLI Interativo

Interface amigável e intuitiva para gerenciar downloads de jurisprudência.

## 🚀 Uso

```bash
cd agentes/jurisprudencia-collector
source .venv/bin/activate
./juri
```

## ✨ Features

### 📊 **Status Dashboard**
- Visualização em tempo real do banco de dados
- Estatísticas de publicações (total, acórdãos, tribunais)
- Tamanho do banco e última atualização
- Status do sistema (Python, dependências)

### 📥 **Download Interativo**

#### Download Retroativo
1. Selecione tribunais (STJ, TJSP)
2. Escolha período:
   - Últimos 7 dias
   - Últimos 15 dias
   - Últimos 30 dias
   - Últimos 90 dias
   - Período personalizado
3. Confirme e execute

**Exemplo de fluxo:**
```
📅 Download Retroativo

Selecione os tribunais:
❯ ◉ ⚖️  STJ (Superior Tribunal de Justiça)
  ◉ 🏛️  TJSP (Tribunal de Justiça de SP)

(↑↓ navegar • espaço selecionar • ⏎ confirmar)

Selecione o período:
❯ 📆 Últimos 7 dias
  📆 Últimos 15 dias
  📆 Últimos 30 dias
  📆 Últimos 90 dias
  📆 Período personalizado

📋 Resumo do Download:
  Período: 2025-11-14 até 2025-11-20
  Tribunais: STJ, TJSP
  Tipos: Acórdão

Confirma execução? (Y/n)
```

### 📊 **Estatísticas**
- Total de publicações
- Acórdãos vs outros tipos
- Tribunais cadastrados
- Tamanho do banco
- Última atualização

## 🎨 Design

Inspirado no **vibe-log-cli**, com:
- ✅ ASCII art logo
- ✅ Painéis coloridos (cyan, magenta, verde)
- ✅ Status indicators (✓/✗)
- ✅ Menu interativo com emojis
- ✅ Navegação clara e intuitiva

## 📦 Dependências

```bash
pip install rich questionary
```

**Auto-instalação:** Se as dependências não estiverem instaladas, o CLI as instala automaticamente na primeira execução.

## 🔧 Funcionalidades (por implementar)

- [ ] Download Diário (hoje)
- [ ] Buscar Publicações
- [ ] Configurações
- [ ] Exportação de dados
- [ ] Integração com RAG

## 🎯 Foco Atual

**Tribunais prioritários:**
- ⚖️  **STJ** - Superior Tribunal de Justiça
- 🏛️  **TJSP** - Tribunal de Justiça de São Paulo

**Tipos de publicação:**
- 📄 **Acórdãos** (foco principal)

---

**Última atualização:** 2025-11-21

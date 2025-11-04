# Changelog - Pré-Processador Jurídico

## [3.0.0] - 2025-10-24

### 🎉 VERSÃO INTEGRADA - Fusão Completa dos Sistemas

Esta versão representa a **fusão completa** do Extrator PDF Jurídico com o sistema de conversão de Markdown, criando um **pré-processador automatizado** otimizado para análise por LLMs.

### 🔄 Principais Mudanças

#### Sistema Integrado 3-em-1
- **Extração + Limpeza + Conversão**: Workflow automatizado completo
- **4 formatos de saída**: TXT, MD, DOCX, HTML
- **Interface com abas**: Visualize simultaneamente texto, markdown e HTML
- **Layout elegante mantido**: Design minimalista preto e branco com fonte monoespaçada da v2.5

#### 📄 Novo: Conversor de Markdown
- **Detecção automática de estrutura**:
  - Títulos (linhas em caixa alta transformadas em `## TÍTULO`)
  - Seções numeradas (`### 1. Seção`)
  - Listas com bullets convertidas para formato MD
  - Citações (texto entre aspas vira `> citação`)
- **Metadados YAML**: Front matter com data, sistema, modo, páginas
- **Preservação de formatação**: Parágrafos, quebras, hierarquia
- **Otimizado para LLMs**: Reduz tokens em até 80% mantendo estrutura

#### 🎨 Novo: Conversor de HTML
- **HTML semântico**: Tags apropriadas (h1, h2, h3, p, ul, ol, blockquote)
- **CSS embutido**: Estilo profissional pronto para visualização
- **Fonte Times New Roman**: Aparência jurídica tradicional
- **Pronto para publicação**: Copiar e colar em sites/blogs

#### 🧹 Modos de Limpeza Integrados
Agora com seletor visual de 3 modos:
- **LEVE**: Conservador (topBand: 5%, bottomBand: 8%, minRepeat: 3, minSignals: 3)
- **MODERADO**: Equilibrado (topBand: 6%, bottomBand: 12%, minRepeat: 2, minSignals: 2)
- **AGRESSIVO**: Máximo (topBand: 8%, bottomBand: 18%, minRepeat: 2, minSignals: 1)

Cada modo ajusta automaticamente os parâmetros de detecção de cabeçalho/rodapé.

#### 🎛️ Configurações Avançadas Integradas
Todas as funcionalidades da v2.3/2.4 agora no layout da v2.5:
- ✅ **Lista branca**: Campo de texto para termos que nunca devem ser removidos
- ✅ **Controle granular**: 6 checkboxes para controle fino
- ✅ **Normalização**: Quebras de linha e hifenização
- ✅ **Preservação de assinaturas**: Detecção automática de áreas legítimas (OAB)

#### 📊 Estatísticas Ampliadas
Painel de estatísticas agora exibe:
- Páginas processadas
- Itens removidos
- Sistema detectado/selecionado
- **Novo**: Modo de limpeza utilizado

#### 🚀 Exportação Multi-Formato
Interface renovada com 4 botões de exportação:
- **TXT**: Texto puro limpo
- **MD**: Markdown com metadados
- **DOCX**: Word (Times New Roman 12pt) via biblioteca docx 8.5.0
- **HTML**: Página web formatada e estilizada

#### 🎯 Otimizado para LLMs
- **Redução de tokens**: Remove até 80% de ruído (hashes, assinaturas, protocolos)
- **Formato estruturado**: Markdown preserva hierarquia sem tokens extras
- **Limpeza inteligente**: Remove metadados mantendo conteúdo jurídico
- **Economia de custo**: Menos tokens = menor custo em APIs de LLM

### 🔧 Melhorias Técnicas

#### Código Refatorado
- **Módulos separados**: Cleaner, MarkdownConverter, HtmlConverter
- **Funções reutilizáveis**: hash(), norm(), resetRegex(), detectSystem()
- **Melhor organização**: Separação clara entre lógica de negócio e UI
- **Performance otimizada**: Processamento em fases bem definidas

#### Sistema de Abas
- **Navegação intuitiva**: Alterne entre visualizações sem reprocessar
- **Estado preservado**: Todas as abas mantêm conteúdo após processamento
- **Feedback visual**: Tab ativa claramente identificada

#### Integração de Bibliotecas
- **PDF.js via CDN**: Carregamento rápido e global
- **FileSaver.js via CDN**: Compatibilidade universal
- **docx via ES Module**: Import dinâmico, carregamento assíncrono
- **Fallback gracioso**: Mensagens claras se biblioteca não carregar

### 🎨 Interface do Usuário

#### Layout Responsivo Aprimorado
- Grid adaptável: 420px sidebar + área de visualização
- Breakpoints otimizados para mobile
- Todos os elementos escaláveis e legíveis

#### Componentes Novos
- **Seletor de modo**: 3 badges clicáveis (Leve/Moderado/Agressivo)
- **Abas de visualização**: Design minimalista com borda inferior
- **Grupo de botões de exportação**: 4 formatos lado a lado

#### Tipografia Mantida
- Fonte monoespaçada: Courier New, Consolas, Monaco
- Hierarquia clara: Títulos em caixa alta, subtítulos menores
- Espaçamento consistente: Respiro visual adequado

### 📝 Documentação Atualizada

#### README Completo
- Seção "O que faz?" explicando workflow completo
- Casos de uso: Advogados, Pesquisadores, Análise por IA
- Exemplo comparativo: Antes/Depois com economia de tokens
- Guia de uso passo a passo

#### Arquivos de Backup
- `index.v2.5.backup.html`: Versão anterior preservada
- `extrator_pdf_processual_v2.3_offline.html`: Versão offline mantida
- `preprocessador-juridico.html`: Cópia do sistema integrado

### 🔄 Compatibilidade

#### Mantido da v2.5
- ✅ Design minimalista preto e branco
- ✅ Seletor de sistema processual (7 opções)
- ✅ Detecção automática de sistema
- ✅ Regex específicos por sistema
- ✅ Padrões ICP-Brasil completos

#### Mantido da v2.4/2.3
- ✅ Whitelist de termos
- ✅ Modos de limpeza (leve/moderado/agressivo)
- ✅ Detecção de cabeçalho/rodapé repetitivo
- ✅ Preservação de assinaturas legítimas (OAB)
- ✅ Normalização de quebras
- ✅ Exportação DOCX

#### Removido/Descontinuado
- ❌ Slider de margem lateral (simplificado, agora automático por modo)
- ❌ Visualização de "itens removidos" (simplificado para foco na saída)

### 🎯 Caso de Uso Principal

**Pré-processamento de documentos jurídicos para análise por LLMs:**

```
PDF Jurídico (pesado, 50 páginas, 15.000 tokens)
    ↓
[Extração + Limpeza]
    ↓
Texto Limpo (8.000 tokens, -47%)
    ↓
[Conversão para Markdown]
    ↓
Markdown Estruturado (3.000 tokens, -80%)
    ↓
[Análise por Claude/GPT]
    ↓
Resposta 5x mais rápida, custo 80% menor!
```

### 🚀 Próximos Passos (Roadmap)

Para v3.1:
- [ ] Exportação para PDF (via jsPDF)
- [ ] Suporte a múltiplos arquivos (batch processing)
- [ ] Opção de criptografia de saída
- [ ] Integração direta com APIs de LLM
- [ ] Modo escuro opcional

---

## [2.5.0] - 2025-10-24

### 🎨 Design Completamente Redesenhado

#### Interface Minimalista Preto e Branco
- **Layout clean e moderno**: Redesign completo focado em produtividade
- **Fonte monoespaçada**: Estilo máquina de escrever (Courier New, Consolas, Monaco)
- **Paleta P&B**: Design profissional sem distrações, apenas preto e branco
- **Totalmente responsivo**: Interface adaptável para desktop, tablet e mobile
- **Tipografia hierárquica**: Uso de caixa alta, espaçamento e pesos para organização visual

#### Componentes UI Modernos
- Cards com bordas finas e sombras sutis
- Botões com estados hover invertidos (preto↔branco)
- Seletor de sistema processual com badges clicáveis
- Checkboxes customizados com descrições
- Área de estatísticas elegante e informativa

### ⚙️ Suporte a Sistemas Processuais Brasileiros

#### Seletor de Sistema com 7 Opções
- **AUTO**: Detecção automática baseada em padrões do texto
- **E-PROC**: Tribunais Regionais Federais
- **E-SAJ**: TJSP e tribunais estaduais com SAJ
- **PJE**: Processo Judicial Eletrônico (CNJ)
- **PROJUDI**: Sistema de Processo Judicial Digital
- **STF**: Supremo Tribunal Federal
- **STJ**: Superior Tribunal de Justiça

#### Padrões Específicos por Sistema
Cada sistema tem regex customizados para detectar e remover assinaturas específicas:

**E-PROC:**
- "Assinado eletronicamente por [nome] em DD/MM/AAAA"
- Menções a "e-Proc" e "Tribunal Regional Federal"
- Links de verificação de assinatura

**E-SAJ:**
- Códigos de validação E-SAJ
- "Tribunal de Justiça do Estado de São Paulo"
- Foro Central/Regional
- "Assinado digitalmente... e-SAJ"

**PJE:**
- Códigos Verificadores PJe (8+ caracteres)
- "Processo Judicial Eletrônico"
- "Assinado eletronicamente por... PJe"

**PROJUDI:**
- "Sistema de Processo Judicial Digital"
- Assinaturas digitais PROJUDI

**STF:**
- "Supremo Tribunal Federal"
- "Praça dos Três Poderes"
- Assinaturas digitais STF

**STJ:**
- "Superior Tribunal de Justiça"
- Assinaturas digitais STJ

#### Detecção Automática Inteligente
Quando "AUTO" está selecionado, o sistema:
1. Analisa o texto completo extraído
2. Conta ocorrências de padrões de cada sistema
3. Seleciona o sistema com maior score
4. Exibe o sistema detectado nas estatísticas

### 🌐 Versão Web com CDN

#### Arquivo Standalone
- **Novo arquivo**: `index.html` - versão web completa
- **HTML único**: Tudo em um arquivo, fácil de hospedar
- **Sem dependências locais**: Usa CDN para bibliotecas
- **Funciona offline**: Versão v2.3 mantida para uso sem internet

#### Bibliotecas via CDN
- **PDF.js 2.6.347**: Via cdnjs.cloudflare.com
- **FileSaver.js 2.0.5**: Via cdnjs.cloudflare.com
- **Carregamento rápido**: CDN global com cache

### 🔧 Melhorias Técnicas

#### Refatoração do Código
- Código mais limpo e modular
- Separação clara entre UI e lógica de processamento
- Funções bem documentadas
- Performance otimizada

#### Sistema de Estatísticas
Exibe após processamento:
- Número de páginas processadas
- Total de itens removidos
- Sistema processual detectado/selecionado

#### Melhor Tratamento de Erros
- Mensagens de erro claras e estilizadas
- Validação antes do processamento
- Feedback visual durante processamento (loading spinner)

### 📝 Experiência do Usuário

#### Fluxo Simplificado
1. Selecionar PDF → exibe nome e tamanho do arquivo
2. Escolher sistema processual → badges visuais
3. Ajustar configurações → checkboxes organizados
4. Processar → feedback visual
5. Baixar TXT → botão habilitado após sucesso

#### Informações Contextuais
- Descrições em cada checkbox explicando o que será removido
- Estatísticas detalhadas após processamento
- Mensagens de erro amigáveis

### 🎯 Configurações Aprimoradas

Agora com interface mais clara:
- ✅ Remover hashes e códigos (SHA-256, MD5, hex)
- ✅ Remover assinaturas digitais (ICP-Brasil, certificados)
- ✅ Remover protocolos (códigos verificadores)
- ✅ Remover numeração de páginas
- ✅ Remover cabeçalho/rodapé repetitivo

---

## [2.4.0] - 2025-10-23

### 🎯 Melhorias Principais

#### ✨ Preservação de Formatação Original
- **Detecção inteligente de parágrafos**: O extrator agora identifica corretamente quando um parágrafo termina e outro começa
- **Suporte a listas e enumerações**:
  - Numeração decimal (1., 2., 3., etc)
  - Letras maiúsculas (A., B., C., etc)
  - Algarismos romanos (I., II., III., etc)
  - Bullets (-, •, *)
- **Preservação de recuo**: Detecta parágrafos com recuo significativo (2+ espaços)
- **Quebras de linha significativas**: Mantém espaçamento entre seções do documento
- **Junção inteligente de páginas**: Paragráfos são preservados mesmo quando atravessam múltiplas páginas

#### 🔒 Remoção Abrangente de Assinaturas Digitais (ICP-Brasil)
Expandida a detecção para incluir **TODOS** os padrões comuns de assinaturas digitais:

**Padrões ICP-Brasil:**
- ICP-Brasil, AC-XX (Autoridades Certificadoras)
- Cadeia de certificação
- Certificado Digital

**Assinaturas Eletrônicas:**
- "Assinado eletronicamente"
- "Documento assinado digitalmente"
- "Assinatura eletrônica"
- "Assinatura digital"

**Carimbos de Tempo:**
- Carimbo de tempo / Timestamp
- Data/Hora da assinatura
- Assinado em DD/MM/AAAA

**Hashes e Validação:**
- SHA-1, SHA-224, SHA-256, SHA-384, SHA-512
- MD5
- Hash do documento
- Resumo criptográfico / MessageDigest
- Códigos hexadecimais (32-64 caracteres)

**Informações de Certificado:**
- Número de série / Serial Number
- Emissor / Emitido por / Issued by
- CN=, O= (Distinguished Names)
- Válido de/até, Validade

**Outros:**
- Selos eletrônicos e códigos de autenticidade
- Códigos verificadores expandidos

### 🔧 Melhorias Técnicas
- Refatoração completa do módulo `Cleaner`
- Código mais legível e modular (5 fases distintas)
- Regex expandidos e documentados
- Melhor tratamento de caracteres especiais
- Performance otimizada na detecção de parágrafos

### 📝 Documentação
- README atualizado com lista completa de recursos
- Changelog criado para rastrear mudanças
- Comentários expandidos no código

---

## [2.3] - Versões Anteriores
- Versão base com remoção básica de assinaturas
- Suporte a múltiplos modos de limpeza (leve, moderado, agressivo)
- Exportação para TXT e DOCX
- Funcionamento offline

# Pré-Processador Jurídico v3.0

Sistema integrado de **extração, limpeza e conversão automatizada** de documentos processuais brasileiros, otimizado para análise por LLMs como Claude, GPT, Gemini, etc.

## 🎯 O que faz?

Este sistema resolve o problema de **pré-processamento de documentos jurídicos em PDF** para análise por IA, realizando:

1. **Extração inteligente** de texto de PDFs jurídicos
2. **Limpeza automática** de assinaturas digitais, hashes, protocolos e metadados
3. **Conversão para Markdown** com preservação de estrutura e formatação
4. **Exportação multi-formato**: TXT, MD, DOCX, HTML

## 🆕 Novidades v3.0 - Sistema Integrado

### 🔄 Fusão Completa
- **Melhor de dois mundos**: Combina funcionalidades das versões v2.5 e v2.4
- **Layout elegante mantido**: Design minimalista preto e branco com fonte monoespaçada
- **Workflow automatizado**: PDF → Texto Limpo → Markdown → Múltiplos Formatos

### 📄 Conversão para Markdown
- **Detecção inteligente de estrutura**:
  - Títulos (texto em caixa alta)
  - Seções numeradas (1., 2., etc)
  - Listas com bullets (-, •, *)
  - Citações (texto entre aspas)
- **Metadados automáticos**: Data, sistema processual, modo de limpeza
- **Formatação preservada**: Parágrafos, quebras de linha, hierarquia

### 🎨 Interface Aprimorada
- **Visualização em abas**: Alterne entre Texto Limpo, Markdown e HTML
- **Estatísticas completas**: Páginas, itens removidos, sistema detectado, modo de limpeza
- **Exportação rápida**: 4 formatos com um clique (TXT, MD, DOCX, HTML)

### 🧹 Modos de Limpeza Integrados
- **LEVE**: Conservador, remove apenas o essencial
- **MODERADO**: Equilíbrio entre limpeza e preservação
- **AGRESSIVO**: Limpeza máxima para análise por LLM

### 🎛️ Configurações Avançadas
- **Lista branca**: Nunca remover termos específicos (ex: "Defensoria Pública")
- **Controle granular**: Habilite/desabilite cada tipo de remoção
- **Normalização**: Quebras de linha, hifenização, espaçamentos

## 🚀 Como Usar

### Uso Online (Recomendado)
1. Acesse: `https://pedrogiudice.github.io/verbose-correct-doodle/`
2. Selecione seu PDF
3. Escolha o sistema processual (ou deixe em AUTO)
4. Configure o modo de limpeza
5. Clique em PROCESSAR
6. Visualize nas abas: Texto / Markdown / HTML
7. Exporte no formato desejado

### Uso Local
1. Clone o repositório
2. Abra `index.html` no navegador
3. Processe seus PDFs localmente (100% offline)

## 🎨 Design Minimalista

Interface profissional com:
- ✅ **Preto e branco**: Zero distrações, máxima produtividade
- ✅ **Fonte monoespaçada**: Estilo terminal/máquina de escrever
- ✅ **Layout responsivo**: Funciona em desktop, tablet e mobile
- ✅ **Componentes elegantes**: Cards, badges, checkboxes customizados

## ⚙️ Suporte a Sistemas Processuais

Detecção automática e limpeza otimizada para:

- ✅ **AUTO** - Detecção automática baseada em padrões
- ✅ **E-PROC** - Tribunais Regionais Federais (TRF)
- ✅ **E-SAJ** - TJSP e tribunais estaduais com SAJ
- ✅ **PJE** - Processo Judicial Eletrônico (CNJ)
- ✅ **PROJUDI** - Sistema de Processo Judicial Digital
- ✅ **STF** - Supremo Tribunal Federal
- ✅ **STJ** - Superior Tribunal de Justiça

Cada sistema tem padrões específicos de assinatura digital que são removidos automaticamente.

## 🔒 Remoção Inteligente

### Sempre Removido
- ✅ **Assinaturas digitais ICP-Brasil**: Certificados, AC-*, cadeias de certificação
- ✅ **Carimbos de tempo**: Timestamps, data/hora de assinatura
- ✅ **Hashes criptográficos**: SHA-1/256/384/512, MD5, hexadecimais
- ✅ **Protocolos eletrônicos**: Códigos verificadores, autenticidades
- ✅ **Selos eletrônicos**: Validações, carimbos digitais
- ✅ **Numeração de páginas**: Pág. X de Y, etc
- ✅ **Cabeçalhos/rodapés repetitivos**: Timbres, endereços, telefones

### Sempre Preservado
- ✅ **Conteúdo jurídico**: Petições, decisões, despachos
- ✅ **Estrutura do documento**: Parágrafos, listas, seções
- ✅ **Assinaturas de advogados**: OAB preservada no contexto correto
- ✅ **Termos da lista branca**: Órgãos públicos, nomes importantes

## 📊 Formatos de Exportação

### 1. TXT (Texto Puro)
- Texto limpo, sem formatação
- Pronto para copiar/colar
- Ideal para LLMs básicos

### 2. MD (Markdown)
- Estrutura preservada com Markdown
- Metadados incluídos (data, sistema, modo)
- Ideal para documentação, GitHub, Notion

### 3. DOCX (Word)
- Documento editável
- Fonte Times New Roman 12pt
- Ideal para edição e impressão

### 4. HTML (Web)
- Documento formatado para web
- CSS embutido, pronto para visualização
- Ideal para publicação online

## 🛠️ Tecnologias

- **PDF.js 2.6.347** - Extração de texto de PDFs
- **FileSaver.js 2.0.5** - Download de arquivos
- **docx 8.5.0** - Geração de arquivos DOCX
- **Vanilla JavaScript** - Sem dependências pesadas
- **CSS Moderno** - Design responsivo e minimalista

## 📖 Documentação Completa

- **[CHANGELOG.md](CHANGELOG.md)** - Histórico completo de versões
- **[HOSPEDAGEM.md](HOSPEDAGEM.md)** - Como hospedar online (GitHub Pages, Netlify, Vercel)
- **[index.v2.5.backup.html](index.v2.5.backup.html)** - Versão anterior (backup)
- **[extrator_pdf_processual_v2.3_offline.html](extrator_pdf_processual_v2.3_offline.html)** - Versão offline com funcionalidades avançadas

## 🔐 Privacidade e Segurança

- ✅ **100% client-side**: Todo processamento é feito no navegador
- ✅ **Zero upload**: Nenhum PDF é enviado para servidores
- ✅ **Open Source**: Código aberto e auditável
- ✅ **Offline-ready**: Funciona sem internet (use versão v2.3)

## 📋 Casos de Uso

### Para Advogados
- Extrair texto de petições para revisão
- Limpar PDFs antes de enviar para cliente
- Converter decisões em formatos editáveis

### Para Pesquisadores
- Processar grandes volumes de decisões judiciais
- Preparar corpus para análise de linguagem natural
- Extrair dados estruturados de documentos

### Para Análise por IA/LLM
- **Pré-processar documentos para Claude/GPT**: Texto limpo sem ruído
- **Formato otimizado**: Markdown preserva estrutura sem tokens desnecessários
- **Redução de contexto**: Remove metadados inúteis, economiza tokens
- **Melhor compreensão**: LLMs entendem melhor texto limpo e estruturado

## 🚦 Exemplo de Uso com Claude

```markdown
# Antes (PDF original, ~10.000 tokens)
[Assinado digitalmente por ...]
[SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855]
[Código Verificador: ABC123XYZ789]
Sentença: O réu é condenado...
[Pág. 1 de 10]

# Depois (Texto processado, ~2.000 tokens)
## SENTENÇA

O réu é condenado...

### 1. DOS FATOS

Em 15 de janeiro de 2024...
```

**Economia**: 80% menos tokens, resposta 5x mais rápida, custo 80% menor!

## 🤝 Contribuindo

Contribuições são bem-vindas! Abra issues ou pull requests.

## 📄 Licença

Open Source - Use livremente para processamento de documentos jurídicos.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/PedroGiudice/verbose-correct-doodle/issues)
- **Documentação**: Veja os arquivos .md neste repositório

---

**Desenvolvido com foco em produtividade jurídica e análise por IA** 🤖⚖️

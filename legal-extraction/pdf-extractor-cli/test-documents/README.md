# Test Documents - Catálogo

Este diretório contém documentos de teste para validação e desenvolvimento do PDF Extractor CLI.

## 📁 Estrutura

```
test-documents/
├── digital/              # PDFs digitais (com camada de texto)
│   ├── pje/             # Documentos do PJE
│   ├── esaj/            # Documentos do ESAJ
│   ├── eproc/           # Documentos do EPROC
│   ├── stf/             # Documentos do STF
│   ├── stj/             # Documentos do STJ
│   └── projudi/         # Documentos do PROJUDI
│
├── scanned/             # PDFs escaneados (sem camada de texto)
│   ├── evidence/        # Provas (contratos, e-mails, etc.)
│   │   ├── contracts/   # Contratos escaneados
│   │   ├── emails/      # E-mails impressos e escaneados
│   │   ├── timesheets/  # Planilhas de horas
│   │   ├── messages/    # Mensagens (WhatsApp, etc.)
│   │   └── screenshots/ # Capturas de tela
│   └── old-documents/   # Documentos antigos escaneados
│
└── output/              # Resultados de testes (gerado automaticamente)
```

## 📝 Como Adicionar Documentos de Teste

### 1. PDFs Digitais (digital/)

Adicione 3-5 PDFs de cada sistema judicial nas respectivas pastas:

- **pje/**: Petições, sentenças, decisões do PJE
- **esaj/**: Documentos do sistema ESAJ (TJSP, etc.)
- **eproc/**: Processos do EPROC (TRFs)
- **stf/**: Decisões e documentos do STF
- **stj/**: Decisões e documentos do STJ
- **projudi/**: Documentos do PROJUDI (estaduais)

**Importante**: Use documentos reais mas **sem dados sensíveis**. Se necessário, redija versões de teste.

### 2. PDFs Escaneados (scanned/)

Adicione 5-10 documentos escaneados de cada tipo:

- **contracts/**: Contratos escaneados (trabalhistas, comerciais, etc.)
- **emails/**: E-mails impressos e depois escaneados
- **timesheets/**: Planilhas de horas, folhas de ponto
- **messages/**: Prints de conversas (WhatsApp, Telegram, etc.)
- **screenshots/**: Capturas de tela de sistemas, apps, etc.
- **old-documents/**: Documentos antigos escaneados (atas, certidões, etc.)

**Objetivo**: Validar OCR (Fase 2) com documentos reais do escritório.

## 📋 Template de Catalogação

Para cada PDF adicionado, documente abaixo:

### Digital - PJE

| Arquivo | Tipo | Páginas | Descrição | Observações |
|---------|------|---------|-----------|-------------|
| `exemplo_peticao_pje.pdf` | Petição | 12 | Petição inicial com assinaturas | Testar remoção de códigos de verificação |
| | | | | |

### Digital - ESAJ

| Arquivo | Tipo | Páginas | Descrição | Observações |
|---------|------|---------|-----------|-------------|
| | | | | |

### Digital - EPROC

| Arquivo | Tipo | Páginas | Descrição | Observações |
|---------|------|---------|-----------|-------------|
| | | | | |

### Digital - STF

| Arquivo | Tipo | Páginas | Descrição | Observações |
|---------|------|---------|-----------|-------------|
| | | | | |

### Digital - STJ

| Arquivo | Tipo | Páginas | Descrição | Observações |
|---------|------|---------|-----------|-------------|
| | | | | |

### Digital - PROJUDI

| Arquivo | Tipo | Páginas | Descrição | Observações |
|---------|------|---------|-----------|-------------|
| | | | | |

### Scanned - Contratos

| Arquivo | Tipo | Páginas | Qualidade | Observações |
|---------|------|---------|-----------|-------------|
| | | | Boa/Média/Ruim | |

### Scanned - E-mails

| Arquivo | Tipo | Páginas | Qualidade | Observações |
|---------|------|---------|-----------|-------------|
| | | | Boa/Média/Ruim | |

### Scanned - Planilhas

| Arquivo | Tipo | Páginas | Qualidade | Observações |
|---------|------|---------|-----------|-------------|
| | | | Boa/Média/Ruim | |

### Scanned - Mensagens

| Arquivo | Tipo | Páginas | Qualidade | Observações |
|---------|------|---------|-----------|-------------|
| | | | Boa/Média/Ruim | |

### Scanned - Screenshots

| Arquivo | Tipo | Páginas | Qualidade | Observações |
|---------|------|---------|-----------|-------------|
| | | | Boa/Média/Ruim | |

### Scanned - Documentos Antigos

| Arquivo | Tipo | Páginas | Qualidade | Observações |
|---------|------|---------|-----------|-------------|
| | | | Boa/Média/Ruim | |

## 🎯 Objetivos de Teste por Fase

### Fase 1 (Atual) - PDFs Digitais

**Validar**:
- ✅ Detecção correta de sistemas judiciais
- ✅ Remoção de assinaturas digitais (PKCS#7, ICP-Brasil)
- ✅ Remoção de códigos de verificação
- ✅ Remoção de selos e carimbos digitais
- ⚠️ Remoção de headers/footers (parcial - melhorar na Fase 2B)

**Comandos de teste**:
```powershell
# Detectar sistema
pdf-extractor detect digital/pje/exemplo.pdf

# Processar e analisar redução
pdf-extractor process digital/pje/exemplo.pdf --with-header

# Validar sistema específico
pdf-extractor process digital/esaj/exemplo.pdf --system ESAJ
```

### Fase 2A - OCR para Escaneados

**Validar**:
- ⏳ Detecção de PDFs escaneados vs digitais
- ⏳ Qualidade de OCR (CER < 5%, WER < 3%)
- ⏳ Performance (tempo por página)
- ⏳ Handling de documentos de baixa qualidade

**Comandos de teste** (após implementação):
```powershell
# Processar escaneado com OCR
pdf-extractor process scanned/contracts/exemplo.pdf --ocr

# OCR com timeout customizado
pdf-extractor process scanned/old-documents/exemplo.pdf --ocr --timeout 90

# Batch de escaneados
pdf-extractor batch scanned/evidence/ --ocr --workers 4
```

### Fase 2B - Headers/Footers Aprimorados

**Validar**:
- ⏳ Remoção de cabeçalhos por sistema
- ⏳ Remoção de rodapés por sistema
- ⏳ Preservação de conteúdo válido (precision > 98%)
- ⏳ Detecção de elementos repetidos

**Análise manual necessária**:
- Comparar output antes/depois visualmente
- Verificar se conteúdo importante foi preservado
- Identificar padrões não cobertos

## 📊 Métricas Esperadas

### PDFs Digitais (Fase 1)

| Sistema | Detecção | Redução Esperada | Observações |
|---------|----------|------------------|-------------|
| PJE | > 80% confidence | 10-20% | Códigos de verificação |
| ESAJ | > 80% confidence | 15-25% | Selos laterais extensos |
| EPROC | > 80% confidence | 10-15% | Assinaturas .p7s |
| STF | > 90% confidence | 20-30% | Marca d'água com CPF |
| STJ | > 90% confidence | 20-30% | Múltiplos elementos |
| PROJUDI | > 60% confidence | 5-15% | Variações regionais |

### PDFs Escaneados (Fase 2A)

| Qualidade | CER | WER | Tempo/Página | Observações |
|-----------|-----|-----|--------------|-------------|
| Boa (300+ DPI) | < 2% | < 1% | 3-5s | Documentos modernos |
| Média (200 DPI) | < 5% | < 3% | 5-8s | Documentos comuns |
| Ruim (< 200 DPI) | < 15% | < 10% | 10-15s | Documentos antigos |

## 🔍 Checklist de Validação

Antes de aprovar cada fase, validar:

### Fase 1
- [ ] Todos os sistemas detectados corretamente (> 80% confidence)
- [ ] Assinaturas digitais removidas (100%)
- [ ] Códigos de verificação removidos (100%)
- [ ] Selos removidos (> 95%)
- [ ] Texto limpo legível e completo

### Fase 2A
- [ ] Scan detection funcional (> 95% accuracy)
- [ ] OCR produz texto legível (CER < 5%)
- [ ] Performance aceitável (< 10s/página)
- [ ] Tratamento de erros robusto
- [ ] Progress bar informativo

### Fase 2B
- [ ] Headers removidos (> 95% recall)
- [ ] Footers removidos (> 95% recall)
- [ ] Conteúdo válido preservado (> 98% precision)
- [ ] Funcionando em todos os sistemas

## 📌 Notas Importantes

1. **Privacidade**: Nunca commitar PDFs com dados sensíveis ao Git
2. **Gitignore**: PDFs estão no .gitignore - são apenas locais
3. **Backup**: Manter cópias dos PDFs de teste originais
4. **Catalogação**: Manter este README atualizado conforme adicionar PDFs
5. **Output**: Pasta `output/` é gerada automaticamente pelos testes

## 🚀 Próximos Passos

1. **Você**: Adicionar 5-10 PDFs de teste em cada categoria
2. **Você**: Preencher tabelas de catalogação acima
3. **Dev**: Implementar Fase 2A (OCR)
4. **Validação**: Testar com seus documentos reais
5. **Dev**: Implementar Fase 2B (Headers/Footers)
6. **Validação final**: Aprovar ou solicitar ajustes

---

**Última atualização**: 2025-11-12 (Estrutura inicial criada)

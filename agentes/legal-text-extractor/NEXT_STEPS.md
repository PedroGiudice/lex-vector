# Legal Text Extractor - Próximos Passos

**Data:** 2025-11-17
**Status:** Fase 1 COMPLETA ✅ | Fase 2 PENDENTE 🚧

---

## ✅ O Que Já Está Pronto (Fase 1)

1. **Estrutura completa implementada** (26 arquivos, ~2300 linhas)
2. **Core de limpeza funcionando** (75+ padrões regex)
3. **Detecção de 7 sistemas judiciais** (auto-detect com confidence scoring)
4. **Extração com pdfplumber** (PDFs com texto)
5. **Exportação TXT/Markdown/JSON**
6. **Venv configurado** (`.venv/` + dependencies instaladas)
7. **Commitado e sincronizado** com repositório

---

## 🚧 O Que Falta Fazer (Fase 2)

### 1. Adicionar PDFs de Teste

**Localização:** `agentes/legal-text-extractor/test-documents/`

Você mencionou que está **separando uma coletânea de documentos**. Adicione:

- [ ] 1 PDF do **STF** (Supremo Tribunal Federal)
- [ ] 1 PDF do **STJ** (Superior Tribunal de Justiça)
- [ ] 1 PDF do **PJE** (Processo Judicial Eletrônico)
- [ ] 1 PDF do **ESAJ** (Sistema de Automação da Justiça)
- [ ] 1 PDF do **EPROC** (Sistema de Processo Eletrônico)
- [ ] 1 PDF do **PROJUDI** (Processo Judicial Digital)
- [ ] 1 PDF **genérico** (judicial sem sistema específico identificável)

**IMPORTANTE:** Os PDFs NÃO serão commitados (estão no `.gitignore`).

---

### 2. Testar Extração Básica

Quando tiver os PDFs, teste a extração:

```bash
# Ativar venv
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/legal-text-extractor
source .venv/bin/activate

# Testar com um PDF
python main.py test-documents/exemplo_pje.pdf

# Deve mostrar:
# - Sistema detectado (PJE, 85%)
# - Redução (15-30%)
# - Texto limpo (primeiros 500 caracteres)
```

**Validações:**
- ✅ Sistema detectado corretamente?
- ✅ Assinaturas/selos removidos?
- ✅ Texto útil preservado? (Art., §, Lei nº, etc)

---

### 3. Implementar Separação de Seções (Claude SDK)

**Arquivo:** `src/analyzers/section_analyzer.py`

**Objetivo:** Usar Claude para identificar e separar peças processuais em documentos de autos.

**Exemplo de input:**
```
PETIÇÃO INICIAL
[Texto da petição...]

CONTESTAÇÃO
[Texto da contestação...]

SENTENÇA
[Texto da sentença...]
```

**Exemplo de output:**
```python
[
    Section(type="petição_inicial", content="...", start_pos=0, end_pos=5000, confidence=0.95),
    Section(type="contestação", content="...", start_pos=5001, end_pos=12000, confidence=0.90),
    Section(type="sentença", content="...", start_pos=12001, end_pos=18000, confidence=0.98)
]
```

**Implementação sugerida:**

1. Criar prompt para Claude identificar delimitadores:
   ```
   Analise este documento judicial e identifique as seções/peças processuais.
   Procure por:
   - PETIÇÃO INICIAL
   - CONTESTAÇÃO
   - RÉPLICA
   - DESPACHO
   - DECISÃO INTERLOCUTÓRIA
   - SENTENÇA
   - AGRAVO, APELAÇÃO, EMBARGOS
   - ACÓRDÃO
   - ATA DE AUDIÊNCIA
   - PARECER DO MP

   Retorne JSON com: {sections: [{type, start_marker, end_marker}]}
   ```

2. Usar Claude API para processar
3. Extrair seções baseado nas posições retornadas
4. Retornar lista de `Section`

**Código a completar:**
```python
def _call_claude(self, text: str) -> str:
    """Chama Claude para análise"""
    message = self.client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Analise este documento judicial e identifique as seções...

            DOCUMENTO:
            {text[:50000]}  # Limitar para não estourar tokens
            """
        }]
    )
    return message.content[0].text
```

---

### 4. Implementar OCR (Fase 2 - Opcional)

**Arquivo:** `src/extractors/ocr_extractor.py`

**Dependências adicionais:**
```bash
pip install paddleocr pdf2image opencv-python
```

**Substituir stub por implementação real:**
```python
from paddleocr import PaddleOCR
from pdf2image import convert_from_path

class OCRExtractor:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='pt')

    def extract(self, pdf_path: Path) -> str:
        # Converter PDF → imagens
        images = convert_from_path(pdf_path)

        # OCR em cada página
        pages_text = []
        for img in images:
            result = self.ocr.ocr(np.array(img), cls=True)
            page_text = "\n".join([line[1][0] for line in result[0]])
            pages_text.append(page_text)

        return "\n\n".join(pages_text)
```

---

### 5. Rodar Bateria de Testes

**Objetivos:**
- Validar com documentos reais
- Medir métricas de qualidade
- Ajustar padrões se necessário

**Comando:**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/legal-text-extractor
source .venv/bin/activate
pytest tests/ -v --cov=src
```

**Métricas esperadas:**
- **Detecção:** >85% confidence para sistemas conhecidos
- **Redução:** 15-30% do tamanho original
- **Preservação:** 100% de elementos jurídicos (Art., §, Lei)
- **Limpeza:** 100% de assinaturas/selos removidos

---

## 🎯 Checklist Completo para Fase 2

### Testes Básicos
- [ ] Adicionar PDFs de teste (7 sistemas)
- [ ] Testar extração de cada sistema
- [ ] Validar detecção automática
- [ ] Validar limpeza (assinaturas removidas?)
- [ ] Validar preservação (elementos jurídicos intactos?)

### Implementações
- [ ] Completar `section_analyzer.py` (Claude SDK)
- [ ] Testar separação de seções
- [ ] (Opcional) Implementar OCR (`ocr_extractor.py`)
- [ ] (Opcional) Testar PDFs escaneados

### Documentação
- [ ] Atualizar README com exemplos reais
- [ ] Documentar métricas obtidas
- [ ] Criar CHANGELOG com resultados da Fase 2

### Integração
- [ ] Testar delegação via legal-braniac
- [ ] Criar exemplo de uso end-to-end
- [ ] (Opcional) Criar CLI básico

---

## 💡 Comandos Úteis

**Ativar venv:**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/legal-text-extractor
source .venv/bin/activate
```

**Testar um PDF:**
```bash
python main.py test-documents/exemplo.pdf
```

**Rodar testes:**
```bash
pytest tests/ -v
```

**Validar sintaxe:**
```bash
python -m py_compile main.py
ruff check src/
mypy src/
```

**Commit changes:**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos
git add .
git commit -m "feat(legal-text-extractor): implementa Fase 2 - separação de seções + testes"
git push
```

---

## 📞 Quando Voltar

**Diga ao Claude:**
> "Estou de volta para continuar a implementação do legal-text-extractor.
> Vou adicionar os PDFs de teste agora. Leia o arquivo NEXT_STEPS.md e me ajude
> a completar a Fase 2."

**Claude vai:**
1. Ler este arquivo
2. Ver quais tasks estão pendentes
3. Te guiar passo a passo pela implementação
4. Testar cada funcionalidade
5. Commitar quando tudo estiver validado

---

## 🎉 Resultado Final Esperado (Fase 2)

**Agente 100% funcional:**
- ✅ Extração de PDFs (texto + escaneados)
- ✅ Detecção de 7 sistemas judiciais
- ✅ Limpeza com 75+ padrões
- ✅ Separação automática de seções (Claude)
- ✅ Exportação TXT/MD/JSON estruturado
- ✅ Métricas validadas com documentos reais
- ✅ Test suite completo
- ✅ Pronto para uso em produção

**Este agente será FUNDAÇÃO para:**
- Agentes de análise jurisprudencial
- Agentes de extração de jurisprudência
- Agentes de análise de teses jurídicas
- Qualquer processamento de documentos jurídicos

---

**Status:** Pronto para continuar quando você voltar! 🚀

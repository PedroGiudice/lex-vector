# Semantic Identity vs Byte Identity

**Data:** 2025-11-25
**Contexto:** Resposta a pergunta do Gordon sobre output do extrator

---

## A Pergunta

> "If you feed the exact same legal text through ESAJ markup vs. PJE markup, should your extractor produce byte-identical output?"

## A Resposta: Semantic Identity, NAO Byte Identity

### Por que NAO byte-identical?

1. **Encoding pode variar**
   - ESAJ pode gerar PDF com UTF-8 NFC
   - PJe pode gerar PDF com UTF-8 NFD
   - Apos normalizacao Unicode, sao semanticamente identicos

2. **Whitespace pode diferir**
   - Sistema A adiciona 2 espacos entre palavras
   - Sistema B adiciona 1 espaco + 1 tab
   - Apos normalizacao, sao identicos

3. **Quebras de linha**
   - Windows: CRLF (`\r\n`)
   - Unix: LF (`\n`)
   - Semanticamente, mesma coisa

### O que DEVE ser identico

| Aspecto | Deve ser identico? | Exemplo |
|---------|-------------------|---------|
| Classificacao | **SIM** | PETICAO_INICIAL = PETICAO_INICIAL |
| Texto semantico | **SIM** | "EXCELENTISSIMO SENHOR" |
| Estrutura logica | **SIM** | Secoes I, II, III |
| Whitespace exato | Nao | `a  b` vs `a b` |
| Encoding exato | Nao | NFC vs NFD |

---

## Implementacao Pratica

### Funcao de Comparacao

```python
def semantic_equal(text1: str, text2: str) -> bool:
    """
    Compara dois textos semanticamente, ignorando diferencas
    de whitespace e encoding.
    """
    def normalize(text: str) -> str:
        # Unicode NFKD (compatibilidade + decomposicao)
        text = unicodedata.normalize("NFKD", text)
        # Remove acentos combinados (opcional, dependendo do caso)
        # text = ''.join(c for c in text if not unicodedata.combining(c))
        # Normaliza whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove espacos nas bordas
        text = text.strip()
        return text

    return normalize(text1) == normalize(text2)
```

### Uso nos Testes

```python
def test_invariance():
    texto_pje = limpar_artefatos(peticao_pje, "PJE")
    texto_esaj = limpar_artefatos(peticao_esaj, "ESAJ")

    # Classificacao DEVE ser identica
    assert classificar(texto_pje) == classificar(texto_esaj)

    # Texto semanticamente igual (nao byte-identical)
    assert semantic_equal(texto_pje, texto_esaj)
```

---

## Por que esta abordagem?

### Robustez

- Tolera variacoes naturais de sistemas diferentes
- Nao falha em casos extremos (encoding exotico, whitespace estranho)
- Reflete o objetivo real: **entendimento semantico**

### Praticidade

- Mais facil de testar
- Menos falsos negativos
- Menos manutencao de fixtures

### Alinhamento com Objetivo

O objetivo do pipeline e:
1. Extrair **conteudo** semantico
2. Classificar **tipo** de documento
3. Permitir **analise** pelo Claude Code

Nenhum desses objetivos requer byte-identity.

---

## Excepcoes

### Quando byte-identity importa

1. **Assinaturas digitais**: Hash do documento deve bater
2. **Validacao juridica**: Documento original intocado
3. **Auditoria**: Reproducibilidade exata

### Nossa posicao

O pipeline de extracao **NAO e ferramenta de validacao juridica**.

Ele e ferramenta de **analise de conteudo**, onde semantic identity e suficiente e preferivel.

---

## Resumo

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   BYTE-IDENTICAL           vs      SEMANTIC-IDENTICAL   │
│   ─────────────                    ──────────────────   │
│                                                         │
│   "abc" == "abc"           vs      "a  bc" ≈ "a bc"    │
│   UTF-8 NFC == UTF-8 NFC   vs      NFC ≈ NFD           │
│                                                         │
│   Uso: Validacao juridica         Uso: Analise de      │
│        Hashes criptograficos           conteudo         │
│                                                         │
│   NOSSO PIPELINE: SEMANTIC-IDENTICAL ✓                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

*Documento criado em resposta a discussao arquitetural com Gordon - 2025-11-25*

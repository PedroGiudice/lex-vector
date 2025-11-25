# Fixtures de Invariancia Multi-Sistema

## Proposito

Estas fixtures testam o principio arquitetural fundamental:

> **A mesma peticao protocolada em PJe, ESAJ, EPROC ou qualquer outro sistema deve produzir classificacao IDENTICA apos remocao de artefatos.**

## Estrutura

```
invariance/
├── peticao_inicial/
│   ├── texto_base.txt          # Conteudo semantico puro (sem artefatos)
│   ├── com_artefatos_pje.txt   # Texto + artefatos PJe simulados
│   ├── com_artefatos_esaj.txt  # Texto + artefatos ESAJ simulados
│   └── com_artefatos_eproc.txt # Texto + artefatos EPROC simulados
│
├── sentenca/
│   └── (mesma estrutura)
│
└── contestacao/
    └── (mesma estrutura)
```

## Uso nos Testes

```python
def test_invariance_peticao_inicial():
    base = Path("fixtures/invariance/peticao_inicial")
    texto_esperado = (base / "texto_base.txt").read_text()

    for sistema in ["pje", "esaj", "eproc"]:
        arquivo = base / f"com_artefatos_{sistema}.txt"
        texto_limpo = limpar_artefatos(arquivo.read_text(), sistema)
        classificacao = classificar(texto_limpo)

        # Classificacao DEVE ser identica
        assert classificacao.category == "PETICAO_INICIAL"

        # Texto limpo deve ser semanticamente igual
        assert normalize_whitespace(texto_limpo) == normalize_whitespace(texto_esperado)
```

## Semantic Identity vs Byte Identity

**Aceitamos diferencas de:**
- Whitespace (espacos extras, tabs vs espacos)
- Encoding (UTF-8 NFC vs NFD, acentos)
- Quebras de linha (\\n vs \\r\\n)

**NAO aceitamos diferencas de:**
- Conteudo semantico
- Classificacao resultante
- Estrutura logica do documento

## Origem dos Textos Base

Os textos base foram extraidos de documentos reais processados pelo pipeline, garantindo 100% de cobertura de casos reais (nao sinteticos).

## Artefatos Simulados

Os artefatos adicionados sao baseados em `src/schemas/validation_artifacts.json`, que documenta todos os padroes conhecidos por sistema.

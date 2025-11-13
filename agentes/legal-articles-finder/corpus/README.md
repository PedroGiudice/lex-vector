# Corpus de Leis Brasileiras

Este diretório contém os textos completos das leis brasileiras para indexação e busca.

## 📚 Leis Suportadas

### Principais Códigos
- **CF**: Constituição Federal de 1988
- **CC**: Código Civil (Lei 10.406/2002)
- **CPC**: Código de Processo Civil (Lei 13.105/2015)
- **CPP**: Código de Processo Penal (Decreto-Lei 3.689/1941)
- **CP**: Código Penal (Decreto-Lei 2.848/1940)
- **CLT**: Consolidação das Leis do Trabalho (Decreto-Lei 5.452/1943)

### Leis Especiais
- **CDC**: Código de Defesa do Consumidor (Lei 8.078/1990)
- **ECA**: Estatuto da Criança e do Adolescente (Lei 8.069/1990)
- **CTN**: Código Tributário Nacional (Lei 5.172/1966)

---

## 📥 Como Obter Textos Completos

### 1. Planalto (Oficial)

```bash
# Constituição Federal
curl http://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm > cf-1988-raw.html

# Código Civil
curl http://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm > cc-2002-raw.html

# CPC
curl http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm > cpc-2015-raw.html
```

### 2. Senado Federal (LexML)

- LexML: https://www.lexml.gov.br/
- Formato TXT disponível para download

### 3. Conversão HTML → TXT

```python
from bs4 import BeautifulSoup

with open('cf-1988-raw.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Extrair apenas texto
text = soup.get_text()

# Limpar e formatar
lines = [line.strip() for line in text.split('\n') if line.strip()]
clean_text = '\n'.join(lines)

with open('cf-1988.txt', 'w', encoding='utf-8') as f:
    f.write(clean_text)
```

---

## 📝 Formato dos Arquivos

### Estrutura Esperada

```
Art. 5º Todos são iguais perante a lei, sem distinção de qualquer natureza, garantindo-se aos brasileiros e aos estrangeiros residentes no País a inviolabilidade do direito à vida, à liberdade, à igualdade, à segurança e à propriedade, nos termos seguintes:

§ 1º As normas definidoras dos direitos e garantias fundamentais têm aplicação imediata.

§ 2º Os direitos e garantias expressos nesta Constituição não excluem outros decorrentes do regime e dos princípios por ela adotados, ou dos tratados internacionais em que a República Federativa do Brasil seja parte.

Art. 6º São direitos sociais a educação, a saúde, a alimentação, o trabalho, a moradia, o transporte, o lazer, a segurança, a previdência social, a proteção à maternidade e à infância, a assistência aos desamparados, na forma desta Constituição.
```

### Regras

1. **Artigos** começam com `Art. N` ou `Artigo N`
2. **Parágrafos** começam com `§ N`
3. **Incisos** começam com algarismos romanos (I, II, III...)
4. **Alíneas** começam com letras (a, b, c...)
5. Manter formatação original (quebras de linha)

---

## 🔧 Indexação

### Indexar Nova Lei

```bash
cd ../src
python main.py index CF "Constituição Federal de 1988" ../corpus/cf-1988.txt 1988
```

### Verificar Indexação

```bash
python main.py stats
```

### Buscar Artigo

```bash
python main.py search CF 5
```

---

## 📊 Status do Corpus

| Lei | Status | Artigos | Última Atualização |
|-----|--------|---------|-------------------|
| CF (1988) | ⚠️ Parcial (template) | ~10 | 2025-11-13 |
| CC (2002) | ❌ Pendente | - | - |
| CPC (2015) | ❌ Pendente | - | - |
| CPP (1941) | ❌ Pendente | - | - |
| CP (1940) | ❌ Pendente | - | - |
| CLT (1943) | ❌ Pendente | - | - |
| CDC (1990) | ❌ Pendente | - | - |
| ECA (1990) | ❌ Pendente | - | - |
| CTN (1966) | ❌ Pendente | - | - |

---

## 📦 Estrutura de Diretórios

```
corpus/
├── README.md                    ← Este arquivo
├── index.db                     ← Banco SQLite (gerado automaticamente)
├── cf-1988.txt                  ← Constituição Federal (template)
├── cc-2002.txt                  ← Código Civil (pendente)
├── cpc-2015.txt                 ← CPC (pendente)
├── cpp-1941.txt                 ← CPP (pendente)
├── cp-1940.txt                  ← CP (pendente)
├── clt-1943.txt                 ← CLT (pendente)
├── cdc-1990.txt                 ← CDC (pendente)
├── eca-1990.txt                 ← ECA (pendente)
└── ctn-1966.txt                 ← CTN (pendente)
```

---

## ⚠️ Observações Importantes

### Copyright e Uso

- **Textos oficiais brasileiros** (leis, decretos, CF) são de **domínio público** conforme Lei 9.610/98, art. 8º, IV.
- Permitido uso comercial e redistribuição.
- Sempre cite a fonte oficial (Planalto, Senado).

### Qualidade dos Textos

- Preferir fontes oficiais (Planalto, Senado)
- Verificar versão consolidada (com todas as emendas/alterações)
- Remover cabeçalhos/rodapés HTML
- Manter numeração original de artigos

### Manutenção

- **Leis são atualizadas** (emendas, alterações)
- Reindexar periodicamente
- Manter log de versões (`cf-1988-v20250113.txt`)

---

## 🔗 Links Úteis

- **Planalto**: http://www.planalto.gov.br/ccivil_03/
- **Senado (LexML)**: https://www.lexml.gov.br/
- **STF**: https://portal.stf.jus.br/
- **STJ**: https://www.stj.jus.br/sites/portalp/Processos/Jurisprudencia

---

**Última Atualização**: 2025-11-13
**Mantido por**: Legal-Braniac Ecosystem

# Revisão: Aquisição de Dados Judiciais do TJSP

## Síntese Executiva

A pesquisa original estava **parcialmente correta** ao afirmar que não existe API oficial do TJSP para decisões em texto integral. No entanto, omitiu uma alternativa funcional e amplamente utilizada: **o web scraping autenticado via pacote `tjsp` de José de Jesus Filho**, que permite downloads em massa de decisões de 1ª e 2ª instância com credenciais de advogado.

---

## Correções à Pesquisa Original

### 1. O que é o JurisMiner

**Erro na pesquisa original**: JurisMiner não foi mencionado.

**Esclarecimento**: O JurisMiner **não é um scraper**. É uma biblioteca de *text mining* para processamento e análise de decisões judiciais já baixadas. Foi desenvolvido pela **ABJ (Associação Brasileira de Jurimetria)** e contém funções para:

- Classificação de decisões (provimento/desprovimento)
- Análise de palavras-chave em contexto (KWIC)
- Cálculo de tempo entre movimentações
- Atribuição de gênero a nomes de partes

**Repositório**: `courtsbr/JurisMiner`

```r
devtools::install_github("courtsbr/JurisMiner")
```

---

### 2. Pacote `tjsp` (jjesusfilho) — Via Funcional para Downloads em Massa

**Omissão crítica na pesquisa original**: Existe um método estabelecido e funcional para obter decisões em texto integral do TJSP.

#### Características do Pacote

| Aspecto | Detalhes |
|---------|----------|
| **Autor** | José de Jesus Filho (PUC-SP, pós-doc USP em jurimetria) |
| **Linguagem** | R |
| **Repositório** | `jjesusfilho/tjsp` |
| **Licença** | MIT |
| **Última atualização** | Versão 2.6.1.9000 (ativo) |

#### Funcionalidades Principais

1. **CJSG (Consulta Julgados 2º Grau)**: Download de acórdãos sem autenticação
2. **CJPG (Consulta Julgados 1º Grau)**: Download do banco de sentenças
3. **CPOSG/CPOPG (Consulta Processual)**: Requer autenticação de advogado

#### Método de Autenticação

O pacote **não utiliza certificado digital A1/A3**. A autenticação é feita via:

1. CPF + senha do cadastro no e-SAJ
2. Token 2FA enviado por email (Gmail ou Outlook)
3. Captura automática do token via integração com `gmailr` ou `Microsoft365R`

```r
library(tjsp)
tjsp_autenticar(
  username = "seu_cpf",
  password = "sua_senha", 
  email_provider = "gmail"  # ou "outlook"
)
```

#### Fluxo de Download de Jurisprudência (2ª Instância)

```r
# 1. Baixar metadados (não requer autenticação)
dir.create("feminicidio")
tjsp_baixar_cjsg(livre = "feminicídio", diretorio = "feminicidio")

# 2. Ler metadados
tabela <- tjsp_ler_cjsg(diretorio = "feminicidio")

# 3. Baixar processos individuais (requer autenticação)
tjsp_baixar_cposg(tabela$processo)

# 4. Extrair dados estruturados
dados <- tjsp_ler_dados_cposg(diretorio = ".")
partes <- tjsp_ler_partes(diretorio = ".")
andamento <- tjsp_ler_movimentacao(diretorio = ".")
decisao <- tjsp_ler_dispositivo(diretorio = ".")
```

---

### 3. Questão do Certificado Digital

**Esclarecimento**: O e-SAJ do TJSP aceita certificado digital A1/A3 para autenticação de advogados no portal web. No entanto, o pacote `tjsp` **não implementa autenticação por certificado digital** — utiliza exclusivamente CPF/senha + 2FA por email.

Para automação com certificado digital, seria necessário desenvolver solução própria usando:
- `requests-pkcs12` (Python) para requisições HTTPS com certificado
- Engenharia reversa dos endpoints do e-SAJ

---

### 4. Posição Ética e Legal do Web Scraping

O autor do pacote `tjsp` destaca pontos importantes:

1. **robots.txt do TJSP não proíbe expressamente scrapers**
2. **Risco de bloqueio de IP** se requisições forem muito frequentes
3. **Não há opção de requisições paralelas** propositalmente
4. **Recomenda-se uso parcimonioso** (preferencialmente à noite)
5. **Destinado a acadêmicos, jornalistas e ONGs** — não para reprodução comercial

---

### 5. Comparativo: Métodos de Acesso ao TJSP

| Método | Texto Integral | Autenticação | Volume | Oficial |
|--------|---------------|--------------|--------|---------|
| Portal e-SAJ (manual) | ✓ Sim | Opcional/Advogado | Baixo | ✓ Sim |
| Pacote `tjsp` (scraper) | ✓ Sim | CPF + 2FA | Alto | ✗ Não-oficial |
| Datajud API | ✗ Metadados | API Key pública | Alto | ✓ Sim |
| WebService e-SAJ | ✓ Sim | Termo de Cooperação | Alto | ✓ Sim |
| MNI/SOAP | — | — | — | ✗ Não disponível |

---

## Recomendação Atualizada para Lakehouse

### Estratégia Híbrida para TJSP

1. **Metadados**: Usar Datajud API (`api_publica_tjsp/_search`)
2. **Texto integral de jurisprudência (2º grau)**: Pacote `tjsp` com `tjsp_baixar_cjsg`
3. **Texto integral de sentenças (1º grau)**: Pacote `tjsp` com credenciais de advogado
4. **Acompanhamento processual**: Pacote `tjsp` autenticado

### Ressalvas Importantes

- O scraping **não é uma API oficial** e pode ser instável
- Alterações no layout do e-SAJ podem quebrar o pacote
- Recomenda-se **rate limiting** (o pacote já implementa delays)
- Para uso comercial intensivo, a via formal (Termo de Cooperação) permanece mais adequada

---

## Ecossistema courtsbr/ABJ

Além do `tjsp`, existem outros pacotes relacionados:

| Pacote | Função |
|--------|--------|
| `courtsbr/esaj` | Scrapers genéricos para sistemas e-SAJ |
| `courtsbr/dje` | Download de Diários de Justiça Eletrônicos |
| `jjesusfilho/stf` | Jurisprudência do STF |
| `courtsbr/stfstj` | Precedentes do STF e STJ |
| `courtsbr/JurisMiner` | Text mining de decisões |

---

## Conclusão

A afirmação de que o TJSP está "efetivamente fechado" para acesso programático sem parceria formal é **excessivamente restritiva**. Embora não exista API oficial, o pacote `tjsp`:

1. Permite downloads em massa funcionais
2. Não requer certificado digital (apenas CPF/senha + email)
3. É mantido ativamente e usado pela comunidade de jurimetria
4. Opera dentro de zona cinzenta legal (não proibido pelo robots.txt)

A escolha entre scraping via `tjsp` e parceria formal depende do caso de uso: pesquisa acadêmica e análises pontuais podem usar o pacote; operações comerciais de alta frequência devem buscar o Termo de Cooperação.

---

## Referências

- Pacote tjsp: https://tjsp.consudata.com.br/
- GitHub jjesusfilho/tjsp: https://github.com/jjesusfilho/tjsp
- GitHub courtsbr: https://github.com/courtsbr
- JurisMiner: https://courtsbr.github.io/JurisMiner/
- Datajud Wiki: https://datajud-wiki.cnj.jus.br/api-publica/

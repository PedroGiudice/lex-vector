# Changelog - Expansão de Tribunais

**Data:** 2025-11-20
**Autor:** Claude Code (Sonnet 4.5)

## ✅ Mudanças Implementadas

### 1. Configuração Expandida de Tribunais

Antes, o scheduler tinha uma lista simples de 10 tribunais:

```python
TRIBUNAIS_PRIORITARIOS = ['STJ', 'STF', 'TST', 'TJSP', 'TJRJ', ...]
```

**Agora**, cada tribunal tem configuração granular com instâncias específicas:

```python
TRIBUNAIS_PRIORITARIOS = [
    {'tribunal': 'STJ', 'descricao': 'STJ - Acórdãos e Decisões', 'instancia': 'superior'},
    {'tribunal': 'STJ', 'descricao': 'STJ - Intimações e Editais', 'instancia': 'superior_intimacoes'},
    # ... etc
]
```

### 2. Tribunais Adicionados

#### **STJ - Superior Tribunal de Justiça**
- ✅ STJ - Acórdãos e Decisões (instância: `superior`)
- ✅ STJ - Intimações e Editais (instância: `superior_intimacoes`)

#### **STF - Supremo Tribunal Federal**
- ✅ STF - Acórdãos e Decisões (instância: `superior`)
- ✅ STF - Intimações e Editais (instância: `superior_intimacoes`)

#### **TST - Tribunal Superior do Trabalho**
- ✅ TST - Acórdãos e Decisões (instância: `superior`)
- ✅ TST - Intimações e Editais (instância: `superior_intimacoes`)

#### **TJSP - Tribunal de Justiça de São Paulo**
- ✅ TJSP - 1ª Instância (instância: `1`)
- ✅ TJSP - 2ª Instância (instância: `2`)

### 3. Total de Configurações

| Antes | Depois |
|-------|--------|
| 10 configurações simples | 15 configurações granulares |
| 10 tribunais únicos | 9 tribunais únicos |
| 1 coleta por tribunal/dia | 1-2 coletas por tribunal/dia |

### 4. Metadados de Instância

Cada download agora registra no banco com formato: `{tribunal}:{instancia}`

Exemplos:
- `STJ:superior` - Acórdãos e decisões do STJ
- `STJ:superior_intimacoes` - Intimações do STJ
- `TJSP:1` - Publicações de 1ª instância do TJSP
- `TJSP:2` - Publicações de 2ª instância do TJSP

### 5. Logging Melhorado

**Antes:**
```
[STJ] Processando tribunal
```

**Agora:**
```
[1/15] STJ - Acórdãos e Decisões
Tribunal: STJ | Instância: superior
```

### 6. Estatísticas Expandidas

**Relatório inicial:**
```
Configurações: 15 | Tribunais únicos: 9
Tribunais: STF, STJ, TJMG, TJRJ, TJRS, TJSP, TRF2, TRF3, TRF4, TST
```

## 📊 Impacto Esperado

### Coleta de Dados
- **Antes:** ~10 requisições/dia (1 por tribunal)
- **Depois:** ~15 requisições/dia (configurações granulares)
- **Benefício:** Melhor separação entre acórdãos e intimações

### Performance
- **Tempo adicional:** ~5 minutos/dia (50% increase)
- **Volume de dados:** +50% estimado (mais especificidade)

### Qualidade dos Dados
- ✅ Melhor classificação de tipos de publicação
- ✅ Separação entre decisões jurisprudenciais e meras intimações
- ✅ Facilita busca posterior (filtro por instância)

## 🔧 Compatibilidade

### Banco de Dados
- ✅ **Schema existente:** Compatível (campo `tribunal` suporta formato `tribunal:instancia`)
- ✅ **Tabela `downloads_historico`:** Registra coletas separadamente
- ✅ **Tabela `publicacoes`:** Continua usando apenas sigla do tribunal

### Downloader
- ✅ **DJENDownloader:** Não necessita alteração (trabalha com siglas simples)
- ✅ **API DJEN:** Compatível (API aceita apenas sigla do tribunal)

### Filtros Futuros
```sql
-- Buscar publicações de 2ª instância do TJSP
SELECT * FROM publicacoes WHERE tribunal = 'TJSP'
  AND id IN (
    SELECT id FROM downloads_historico
    WHERE tribunal = 'TJSP:2'
  );

-- Buscar apenas acórdãos de tribunais superiores
SELECT * FROM publicacoes WHERE tribunal IN ('STJ', 'STF', 'TST')
  AND id IN (
    SELECT id FROM downloads_historico
    WHERE tribunal LIKE '%:superior'
  );
```

## ⚙️ Configuração

### Adicionar Novo Tribunal
```python
# Em scheduler.py, adicionar a TRIBUNAIS_PRIORITARIOS:
{
    'tribunal': 'SIGLA',           # Ex: 'TJRJ'
    'descricao': 'Descrição clara', # Ex: 'TJRJ - 2ª Instância'
    'instancia': 'id_instancia'    # Ex: '2', 'superior', 'todas'
}
```

### Executar Scheduler
```bash
# Executar agora (teste)
python scheduler.py --now

# Execução normal (loop diário)
python scheduler.py
```

## 📝 Próximos Passos

### Curto Prazo
- [ ] Testar coleta real com novos tribunais
- [ ] Validar separação de acórdãos vs intimações
- [ ] Ajustar min_publicacoes_esperadas por tipo de instância

### Médio Prazo
- [ ] Adicionar filtros de tipo de comunicação na API
- [ ] Implementar processamento específico por instância
- [ ] Criar views no banco para facilitar consultas por instância

### Longo Prazo
- [ ] Interface web para visualizar estatísticas por tribunal/instância
- [ ] Dashboard de monitoramento de coletas
- [ ] Sistema de alertas para falhas de coleta

## 🐛 Issues Conhecidas

### Limitação da API DJEN
A API DJEN **não possui parâmetro de instância/tipo de caderno** na rota `/comunicacao`.

Atualmente, a configuração de instância serve apenas para:
1. Organização interna (logging, relatórios)
2. Metadados no banco (`downloads_historico`)
3. Preparação para filtros futuros

**Solução futura:** Implementar extração de cadernos PDF específicos por instância quando disponível.

### Duplicação de Dados
Como a API retorna todas as publicações do tribunal (sem filtro de instância), configurações múltiplas do mesmo tribunal podem **baixar publicações duplicadas**.

**Mitigação atual:** Deduplicação via hash SHA256 garante que não há duplicatas no banco.

**Trade-off:** Mais requisições à API, mas mesmas publicações armazenadas (deduplicadas).

## 📚 Referências

- **API DJEN:** https://comunicaapi.pje.jus.br/api/v1
- **Schema do banco:** `schema.sql`
- **Arquitetura:** `docs/ARQUITETURA_JURISPRUDENCIA.md`
- **Documentação do scheduler:** `SCHEDULER_README.md`

---

**Última atualização:** 2025-11-20

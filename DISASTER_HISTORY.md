# DISASTER HISTORY

Periodo: 03-04/11/2025 | Duracao: 3 dias | Status: Resolvido

---

## Causa Raiz

Codigo em HD externo + ambiente dinamico = indeterminismo.
Debugging de sintomas (PATH, hooks, npm) ao inves de arquitetura.

---

## 7 Licoes

| # | Licao | Solucao |
|---|-------|---------|
| 1 | Separacao de camadas | Codigo (Git), Ambiente (.venv local), Dados (~/claude-code-data/) |
| 2 | Sem symlinks absolutos | Falham entre maquinas |
| 3 | PATH limpo | Apenas diretorios de binarios |
| 4 | Hooks dinamicos | Sem caminhos hardcoded |
| 5 | 5 Porques primeiro | Identificar causa raiz antes de corrigir |
| 6 | venv obrigatorio | Todo projeto Python |
| 7 | Git diario | Commit/push ao fim, pull ao iniciar |

---

## Comandos Bloqueados

```bash
cp *.py ~/claude-code-data/      # codigo para area de dados
pip install <pkg>                 # sem venv ativo
ln -s /path/absoluto/usuario      # symlinks nao portaveis
```

---

## Regra de Ouro

> 2h sem progresso? Pare. Aplique 5 Porques. Esta tratando sintoma.

---

## Tecnica dos 5 Porques

```
Sintoma → Por que? → Por que? → Por que? → Por que? → CAUSA RAIZ
                                                        ↑
                                                   Corrigir apenas isto
```

---

Documentado: 07/11/2025 | Autor: PedroGiudice

---
name: block-backup-files
enabled: true
event: file
pattern: \.(old|bak|backup|orig|tmp|copy)$|_(antigo|backup|old)\.|_antigo$|_backup$|_old$|\.backup\.
action: block
---

**BLOQUEADO: Arquivo de backup detectado**

Criar arquivos de backup no repositorio e **PROIBIDO**.

**Padroes bloqueados:**
- `.old`, `.bak`, `.backup`, `.orig`, `.tmp`, `.copy`
- `_antigo`, `_backup`, `_old`

**O que fazer:**
1. Use `git stash` para salvar mudancas temporarias
2. Use `git branch` para criar uma branch de backup
3. Use `git commit` para versionar antes de grandes mudancas

**Se precisar preservar codigo antigo:**
```bash
git checkout -b backup/nome-descritivo
git add . && git commit -m "backup: preservando estado antes de X"
git checkout main
```

> Regra definida em: .claude/hookify.block-backup-files.local.md

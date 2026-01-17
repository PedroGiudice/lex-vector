# Doc Assembler Upload Fix - Plano de Implementacao

> **Para Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para implementar este plano tarefa por tarefa.

**Goal:** Corrigir o upload de arquivos do Doc Assembler que falha no Linux Chrome (funciona no Windows).

**Arquitetura:** O problema esta no encoding multipart/form-data. O Axios client estava configurado com `Content-Type: application/json` como padrao, que interfere com FormData. O browser Linux Chrome nao consegue sobrescrever isso corretamente, resultando em arquivos corrompidos (0 bytes).

**Tech Stack:** React + TypeScript, Axios, FastAPI, python-docx

---

## Diagnostico do Problema

**Sintomas:**
1. Upload funciona no Windows Chrome
2. Upload falha no Linux Chrome - arquivo chega com 0 bytes ou corrompido
3. Backend retorna 500: `PackageNotFoundError: Package not found at '/tmp/builder_uploads/xxx.docx'`
4. Cache do navegador Linux mantem JS antigo (funciona em incognito)

**Causa Raiz:**
O Axios client em `api.ts` foi criado com `Content-Type: application/json`. Quando usamos `this.client.post()` com FormData, esse header persiste e corrompe o boundary do multipart encoding.

**Solucao:**
1. Usar `axios.post()` diretamente (sem o client pre-configurado) para uploads
2. Nao definir Content-Type - deixar o browser calcular o boundary automaticamente
3. Adicionar cache-busting headers no frontend build

---

## Fase 1: Verificar e Consolidar Mudancas Pendentes

### Task 1: Reverter mudancas e comecar do zero

**Por que:** Ha mudancas nao commitadas que podem estar incompletas ou inconsistentes. Melhor reverter e fazer de forma estruturada.

**Step 1: Verificar estado atual**

```bash
cd /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench
git status --short
git diff --stat
```

**Step 2: Reverter mudancas nao commitadas**

```bash
git checkout -- docker/services/doc-assembler/api/builder_routes.py
git checkout -- frontend/src/services/api.ts
```

**Step 3: Verificar revert funcionou**

```bash
git status --short
# Expected: limpo, sem modificacoes nesses arquivos
```

---

## Fase 2: Fix do Frontend (Causa Raiz)

### Task 2: Corrigir uploadDocument para usar axios diretamente

**Files:**
- Modify: `frontend/src/services/api.ts:18-32`

**Step 1: Ler o arquivo atual**

```bash
cat frontend/src/services/api.ts
```

**Step 2: Aplicar a correcao**

Substituir o metodo `uploadDocument`:

```typescript
async uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  // CRITICAL: Use axios directly, NOT this.client
  // this.client has default Content-Type: application/json which corrupts FormData
  // Browser must set Content-Type with correct multipart boundary automatically
  const response = await axios.post<UploadResponse>(
    `${API_BASE}/upload`,
    formData
    // No headers - browser sets Content-Type: multipart/form-data; boundary=...
  );

  return response.data;
}
```

**Step 3: Verificar sintaxe**

```bash
cd frontend && bun run build
```

Expected: Build passa sem erros

**Step 4: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "fix(lw-doc-assembler): use axios directly for FormData upload

The pre-configured client had Content-Type: application/json default
which corrupted multipart/form-data encoding on Linux Chrome.
Using axios.post() directly lets browser set correct boundary.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Fase 3: Backend Logging (Para Debug Futuro)

### Task 3: Adicionar logging estruturado ao upload endpoint

**Files:**
- Modify: `docker/services/doc-assembler/api/builder_routes.py:1-20` (imports)
- Modify: `docker/services/doc-assembler/api/builder_routes.py:354-428` (endpoint)

**Step 1: Adicionar imports de logging**

Adicionar apos linha 11 (apos `import shutil`):

```python
import logging
import traceback

logger = logging.getLogger(__name__)
```

**Step 2: Adicionar logging no upload_document**

Adicionar no inicio do endpoint (apos docstring):

```python
# Log request metadata for debugging
logger.info(
    "Upload request: filename=%s, content_type=%s, size=%s",
    file.filename, file.content_type, file.size
)
```

Adicionar apos `content = await file.read()`:

```python
logger.info(
    "File content: size=%d bytes, first_bytes=%s",
    len(content), content[:20].hex() if content else "empty"
)
```

Adicionar no except block:

```python
logger.error(
    "Upload failed: %s\n%s", str(e), traceback.format_exc()
)
```

**Step 3: Commit**

```bash
git add docker/services/doc-assembler/api/builder_routes.py
git commit -m "feat(lw-doc-assembler): add structured logging to upload endpoint

Logs request metadata and file content size for debugging upload issues.
Includes full traceback on errors.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Fase 4: Deploy e Teste

### Task 4: Deploy do frontend

**Step 1: Build local**

```bash
cd /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/frontend
bun run build
```

**Step 2: Sync para Oracle Cloud**

```bash
rsync -avz --delete dist/ opc@64.181.162.38:/home/opc/lex-vector/legal-workbench/frontend/dist/
```

**Step 3: Rebuild container**

```bash
ssh opc@64.181.162.38 "cd /home/opc/lex-vector/legal-workbench && docker compose build frontend-react && docker compose up -d frontend-react"
```

**Step 4: Verificar deploy**

```bash
ssh opc@64.181.162.38 "docker logs legal-workbench-frontend-react-1 --tail 5"
```

### Task 5: Deploy do backend

**Step 1: Sync arquivos**

```bash
rsync -avz docker/services/doc-assembler/ opc@64.181.162.38:/home/opc/lex-vector/legal-workbench/docker/services/doc-assembler/
```

**Step 2: Rebuild container**

```bash
ssh opc@64.181.162.38 "cd /home/opc/lex-vector/legal-workbench && docker compose build api-doc-assembler && docker compose up -d api-doc-assembler"
```

**Step 3: Verificar logs**

```bash
ssh opc@64.181.162.38 "docker logs legal-workbench-api-doc-assembler-1 --tail 10"
```

### Task 6: Teste E2E

**Step 1: Limpar cache do navegador**

Usuario deve:
1. Abrir Chrome DevTools (F12)
2. Clicar direito no botao Reload
3. Selecionar "Empty Cache and Hard Reload"

**Step 2: Testar upload**

1. Navegar para http://64.181.162.38/doc-assembler
2. Clicar em "Upload Document"
3. Selecionar arquivo DOCX (ex: `Novartis_Acao_Monitoria_Guilherme_Higino_Lima.docx`)
4. Verificar que o conteudo aparece na tela

**Step 3: Verificar logs do backend**

```bash
ssh opc@64.181.162.38 "docker logs legal-workbench-api-doc-assembler-1 --tail 20 | grep -i upload"
```

Expected: Log mostrando `size=XXXXX bytes` (nao zero)

---

## Verificacao Final

- [ ] Frontend build passa
- [ ] Backend inicia sem erros
- [ ] Upload funciona no Linux Chrome (navegador normal)
- [ ] Upload funciona no Windows Chrome
- [ ] Logs mostram tamanho correto do arquivo

---

## Rollback (se necessario)

```bash
# Reverter frontend
git revert HEAD~1  # se Task 2 foi o ultimo commit

# Reverter backend
git revert HEAD~1  # se Task 3 foi o ultimo commit

# Redeploy
# Seguir Tasks 4-5 novamente
```

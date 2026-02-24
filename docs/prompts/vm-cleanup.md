# VM Cleanup e Migracao para Object Storage

## Objetivo

Varredura completa da VM Contabo (193GB disco). Liberar espaco, mover dados frios pro Object Storage S3-compatible (250GB Contabo).

## Acoes

1. **Mover `/home/opc/juridico-data/stj/` (33GB) pro Object Storage.** Esses dados brutos ja foram processados (scan + chunk no SQLite). Manter copia remota, remover local.

2. **Auditar e limpar:**
   - `.cache/` residual (uv, huggingface, etc)
   - `.local/share/` (5.7GB -- o que e?)
   - `Android/Sdk/` (2.7GB -- nao usa mobile)
   - `sfdc/` (1.4GB -- documentos juridicos antigos, mover pro S3?)
   - `claude-devtools/` (1GB)
   - `claude-config/debug/` (187MB)
   - Build artifacts: `target/`, `node_modules/`, `.next/`, `dist/`

3. **Configurar Object Storage S3:**
   - Credenciais em `~/.aws/credentials` ou env vars
   - Bucket dedicado pra dados juridicos
   - Testar com `aws s3 cp` ou `rclone`

4. **Meta:** manter disco abaixo de 60% uso (< 116GB ocupados).

## Dados que NAO podem ser removidos

- `lex-vector/stj-vec/db/stj-vec.db` (~31GB+) -- DB com chunks e embeddings
- Chunks JSONL no Modal Volume `stj-vec-data` -- ja estao la, nao local
- Repos ativos: lex-vector, ELCO-machina, ADK-sandboxed-legal, .claude

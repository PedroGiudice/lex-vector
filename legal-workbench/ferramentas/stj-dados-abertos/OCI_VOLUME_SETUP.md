# Configuracao de Volume de Bloco OCI

Guia para provisionar armazenamento persistente para o STJ Dados Abertos.

---

## Requisitos

| Recurso | Especificacao |
|---------|---------------|
| Volume Size | 100GB minimo (50GB dados + margem) |
| Performance | Balanced ou Higher Performance |
| Availability Domain | Mesma da VM (SA-SAOPAULO-1-AD-1) |

---

## Passo 1: Criar Volume no OCI Console

1. Acesse: OCI Console > Storage > Block Volumes
2. Create Block Volume:
   - Name: `juridico-data-stj`
   - Compartment: (seu compartment)
   - Availability Domain: SA-SAOPAULO-1-AD-1
   - Volume Size: 100 GB
   - Volume Performance: Balanced (10 VPUs)
   - Encryption: Oracle-managed keys

---

## Passo 2: Anexar Volume a Instancia

1. Va para: Compute > Instances > (sua instancia)
2. Resources > Attached Block Volumes > Attach Block Volume
3. Configurar:
   - Volume: juridico-data-stj
   - Attachment Type: Paravirtualized
   - Access: Read/Write
   - Device Path: /dev/oracleoci/oraclevdb (ou deixar automatico)

4. Aguardar status: Attached

---

## Passo 3: Configurar na VM

### 3.1 SSH na VM

```bash
ssh opc@100.114.203.28  # Via Tailscale
```

### 3.2 Verificar device anexado

```bash
lsblk
# Procurar novo device (ex: sdb, 100G)
```

### 3.3 Executar script de provisionamento

```bash
cd /home/opc/lex-vector/legal-workbench/ferramentas/stj-dados-abertos
sudo ./scripts/provision-oci-volume.sh /dev/sdb
```

### 3.4 Configurar variaveis de ambiente

```bash
# Adicionar ao ~/.bashrc
echo 'export DATA_PATH=/mnt/juridico-data/stj' >> ~/.bashrc
echo 'export DB_PATH=/mnt/juridico-data/stj/database/stj.duckdb' >> ~/.bashrc
source ~/.bashrc
```

---

## Passo 4: Verificar Configuracao

```bash
# Verificar mount
df -h /mnt/juridico-data

# Verificar estrutura
ls -la /mnt/juridico-data/stj/

# Testar CLI
cd /home/opc/lex-vector/legal-workbench/ferramentas/stj-dados-abertos
source .venv/bin/activate
python cli.py stj-info
```

Output esperado:
```
Paths:
  Data Root: /mnt/juridico-data/stj
  Staging: /mnt/juridico-data/stj/staging
  Database: /mnt/juridico-data/stj/database/stj.duckdb
  Logs: /mnt/juridico-data/stj/logs
  Acessivel: Sim
```

---

## Passo 5: Download Inicial

Apos confirmar que tudo esta funcionando:

```bash
# Download MVP (30 dias, Corte Especial)
python cli.py stj-download-mvp

# Download completo por periodo
python cli.py stj-download-periodo 2022-05-01 $(date +%Y-%m-%d) --orgao corte_especial
```

---

## Troubleshooting

### Volume nao aparece apos anexar

```bash
# Rescan SCSI
sudo sh -c 'echo "- - -" > /sys/class/scsi_host/host*/scan'
lsblk
```

### Permissao negada

```bash
sudo chown -R opc:opc /mnt/juridico-data
```

### Mount nao persiste apos reboot

Verificar /etc/fstab:
```bash
cat /etc/fstab | grep juridico
```

Deve conter linha similar a:
```
UUID=xxxxx /mnt/juridico-data xfs defaults,noatime,_netdev 0 0
```

---

## Custos Estimados (OCI)

| Recurso | Custo/mes (USD) |
|---------|-----------------|
| Block Volume 100GB Balanced | ~$2.50 |
| Object Storage Backup (opcional) | ~$0.02/GB |

---

## Informacoes da VM Atual

| Atributo | Valor |
|----------|-------|
| Hostname | lw-pro |
| IP Tailscale | 100.114.203.28 |
| IP Publico | 64.181.162.38 |
| Regiao | sa-saopaulo-1 |
| AD | SA-SAOPAULO-1-AD-1 |

---

*Atualizado: 2026-02-04*

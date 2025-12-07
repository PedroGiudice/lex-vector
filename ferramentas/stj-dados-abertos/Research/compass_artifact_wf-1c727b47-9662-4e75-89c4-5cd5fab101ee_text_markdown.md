# Brazilian Judicial Data Lakehouse: STJ & TJSP Acquisition Architecture

**Bottom Line**: STJ offers excellent official full-text access via CKAN-based open data portal with daily updates—**use static file downloads for both historical backfill and incremental loads**. TJSP presents a critical gap: **no official API or bulk export exists for full-text decisions**; the only legitimate path requires a formal Cooperation Agreement (Termo de Cooperação). For metadata across both courts, the Datajud API provides unified REST access with a public API key.

---

## Executive summary: Recommended stack by tribunal

For a Data Lakehouse requiring **full-text judicial decisions** through official channels only, the reality is asymmetric:

**STJ (Achievable)**: Deploy the Portal de Dados Abertos CKAN downloads as your primary source. The "Íntegras de Decisões Terminativas e Acórdãos" dataset provides ZIP files containing full decision text with JSON metadata, updated **daily (T+1 after DJe publication)**. No authentication required. Historical data available from **February 2022 forward only**—earlier decisions require alternative approaches.

**TJSP (Blocked)**: There is currently **no official programmatic path** to acquire full-text decisions without a formal partnership. TJSP uses SAJ/e-SAJ (not PJe), has no public MNI endpoint, and their WebService integration requires signing a Cooperation Agreement. Contact `sti.apoiojud@tjsp.jus.br` to initiate partnership discussions. Meanwhile, use Datajud API for metadata cataloging.

---

## STJ data acquisition: Files decisively beat API

The definitive verdict for STJ is **static file downloads for both bulk historical load and incremental updates**. Here's why:

The STJ Portal de Dados Abertos at `https://dadosabertos.web.stj.jus.br/` runs on CKAN (Comprehensive Knowledge Archive Network) and provides **18 datasets** including the critical "Íntegras de Decisões Terminativas e Acórdãos do Diário da Justiça" at `https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica`. This dataset contains full decision text for acórdãos and terminative monocratic decisions published in the Diário da Justiça.

The file structure follows a logical naming convention: monthly consolidations (`AAAAMM.zip`) for initial backfill, then daily files (`AAAAMMDD.zip`) with corresponding metadata (`metadadosAAAAMMDD.json`). Each ZIP contains the actual decision text files. **No REST API exists for live queries**—the Datajud API at `https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search` provides only process metadata (capas processuais, movimentações), never full text.

| Acquisition Method | Full Text | Historical Depth | Query Flexibility | Auth Required |
|-------------------|-----------|-----------------|-------------------|---------------|
| CKAN File Downloads | ✓ Yes | Feb 2022+ | Download all, filter locally | None |
| Datajud REST API | ✗ Metadata only | Broader history | Elasticsearch DSL | Public API key |

For **5-year historical backfill**: Download monthly ZIPs from February 2022 through mid-2022, then daily files onward. For decisions **prior to February 2022**, you'll need supplementary approaches—either the "Espelhos de Acórdãos" dataset (which contains ementas rather than full íntegras) or Datajud metadata combined with tribunal-specific consultations.

**CKAN API endpoints** for programmatic access:
```
Base: https://dadosabertos.web.stj.jus.br/api/3/action/
package_list - enumerate all datasets
package_show?id=integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica - get resource URLs
```

---

## TJSP front door: Closed without formal partnership

TJSP represents the primary architectural challenge. After extensive investigation, **three potential entry points all lead to barriers**:

**MNI (Modelo Nacional de Interoperabilidade)**: TJSP runs SAJ/e-SAJ (Softplan), not PJe (CNJ standard). While MNI integration with SAJ "is under implementation" per technical discussions, **no publicly accessible WSDL endpoint exists**. Reference courts like TJPE expose MNI at URLs like `https://pjemni.app.tjpe.jus.br/2g/servico-intercomunicacao-2.2.2?wsdl`, but TJSP has no equivalent. The CNJ MNI 3.0 WSDL at `https://www.cnj.jus.br/wp-content/uploads/conteudo/arquivo/2019/10/servico-intercomunicacao.wsdl` defines the standard, but TJSP hasn't exposed a conforming endpoint.

**ESAJ WebService**: An integration pathway exists but is **gated by Cooperation Agreement**. According to TJSP documentation, production WebService access requires formal partnership—currently available primarily to government entities (Prefeituras, Autarquias) for Execução Fiscal proceedings. The required certificate is A1 (e-CNPJ) for system authentication.

**Portal de Dados Abertos**: Unlike STJ, **TJSP has no open data portal for judicial decisions**. Downloads at `https://www.tjsp.jus.br/PrimeiraInstancia/Download/Default` contain administrative forms and templates, not decision bulk exports.

The **only viable official path** is formal partnership:
- Contact: `sti.apoiojud@tjsp.jus.br`  
- Prepare justification (research purposes, business case)
- Expect credential-based authentication post-agreement
- Monitor TJSP Resolution 963/2025 indicating transition to eProc system, which may eventually expose MNI endpoints

---

## Authentication architecture: A1 certificates enable automation

**Clear verdict**: Use **A1 certificates (software-based)** for any automated server access. A3 hardware tokens are incompatible with unattended server operations.

The distinction matters for ICP-Brasil compliance:

| Certificate Type | Storage | Validity | Automation Compatible | Typical Cost |
|-----------------|---------|----------|----------------------|--------------|
| A1 | .pfx/.p12 file | 12 months | ✓ Yes - file-based | R$120-250/year |
| A3 | USB token/SmartCard | 12-36 months | ✗ No - requires physical device | R$150-500 |

**By tribunal**:
- **STJ Dados Abertos**: No authentication required (open access)
- **Datajud API**: Public API key only—`Authorization: APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==` (verify current key at `https://datajud-wiki.cnj.jus.br/api-publica/acesso`)
- **TJSP e-SAJ**: Both A1 and A3 accepted per Resolution TJSP 551/2011, Art. 4º, I—**A1 recommended for automation**
- **MNI SOAP**: Username/password (`idConsultante`/`senhaConsultante`) in SOAP envelope, no certificate

Python implementation for A1 certificates:
```python
from requests_pkcs12 import post

response = post(
    url='https://webservice.tribunal.jus.br/api/endpoint',
    pkcs12_filename='/path/to/certificate.pfx',
    pkcs12_password='cert_password',
    data={'param': 'value'}
)
```

Authorized certificate providers: **Certisign**, **Serasa Experian**, **SERPRO** (government), **Valid**, **Soluti**—all must be ICP-Brasil accredited.

---

## Documentation links and technical references

**STJ Resources**:
- Portal de Dados Abertos: `https://dadosabertos.web.stj.jus.br/`
- Íntegras Dataset: `https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica`
- CKAN API Docs: `https://docs.ckan.org/en/2.9/api/`
- Plano de Dados Abertos: `https://bdjur.stj.jus.br/jspui/bitstream/2011/163765/plano_dados_abertos_stj.pdf`

**Datajud/CNJ Resources**:
- API Wiki: `https://datajud-wiki.cnj.jus.br/api-publica/`
- Tutorial PDF: `https://www.cnj.jus.br/wp-content/uploads/2023/05/tutorial-api-publica-datajud-beta.pdf`
- MNI 3.0 WSDL: `https://www.cnj.jus.br/wp-content/uploads/conteudo/arquivo/2019/10/servico-intercomunicacao.wsdl`
- MNI Package: `https://www.cnj.jus.br/wp-content/uploads/2015/03/mni-3.0.0.zip`

**TJSP Resources**:
- Jurisprudence (2nd Instance): `https://esaj.tjsp.jus.br/cjsg/resultadoCompleta.do`
- DJE Download: `https://www.dje.tjsp.jus.br`
- Integration Contact: `sti.apoiojud@tjsp.jus.br`

---

## Python library recommendations

For **CKAN/REST operations**:
```python
import requests  # Standard HTTP client
import ckanapi    # CKAN-specific wrapper: pip install ckanapi
```

For **SOAP/MNI operations** (when TJSP eventually exposes endpoints):
```python
from zeep import Client  # Modern SOAP: pip install zeep
# Alternative: suds-community for legacy compatibility
```

For **certificate handling**:
```python
from requests_pkcs12 import get, post  # pip install requests-pkcs12
from cryptography import x509  # Certificate inspection
```

For **Elasticsearch queries** (Datajud):
```python
from elasticsearch import Elasticsearch  # pip install elasticsearch
# Or use requests directly with POST to /_search endpoint
```

---

## Rate limits and operational gotchas

**No explicit rate limits are documented** for either STJ CKAN or Datajud API. However, observe these constraints:

- **Datajud pagination**: Maximum **10,000 results per request**. Use `search_after` parameter with `@timestamp` sort for bulk extraction
- **CKAN downloads**: Implement exponential backoff for bulk file retrieval
- **Historical gap**: STJ full-text íntegras only available from **February 2022**—earlier decisions require alternative sourcing
- **Datajud API key**: The public key may change; always verify at `https://datajud-wiki.cnj.jus.br/api-publica/acesso`
- **DJEN (Diário de Justiça Eletrônico Nacional)**: Provides full text at `https://comunica.pje.jus.br/` but has **no documented API**—web interface only

---

## Hidden gems for full-text decisions

Several non-obvious official sources merit investigation:

**LexML Brasil** at `https://www.lexml.gov.br/` provides OAI-PMH metadata harvesting and URN-based persistent identifiers. While it stores **links rather than full text**, it offers discovery across all Brazilian jurisprudence with stable identifiers for data lakehouse integration.

**Tribunal-specific Open Data Portals**: Some TJs beyond STJ expose MNI endpoints. TJPE, for example, publishes endpoints at `https://pjemni.app.tjpe.jus.br/2g/servico-intercomunicacao-2.2.2?wsdl`. Investigate each target tribunal's transparency portal.

**STJ DJe XML Format**: Beyond ZIP downloads, STJ's Diário da Justiça Eletrônico offers XML format suitable for structured parsing—check the transparency portal for access.

**Academic Research Agreements**: Per Resolução CNJ 215/2015, Art. 34, formal research partnerships can unlock access to otherwise restricted data, including sealed cases under strict anonymization requirements. Contact the **Departamento de Pesquisas Judiciárias (DPJ/CNJ)** for research-grade access.

**Domicílio Judicial Eletrônico**: At `https://www.cnj.jus.br/tecnologia-da-informacao-e-comunicacao/justica-4-0/domicilio-judicial-eletronico/`, this provides push API integration for entities receiving judicial communications—useful if building systems for specific parties rather than general research.

---

## Conclusion

The Brazilian judicial data acquisition landscape presents a clear asymmetry: **STJ offers production-ready infrastructure** with daily-updated full-text downloads requiring no authentication, while **TJSP remains effectively closed** to programmatic full-text access without formal partnership. Your optimal architecture deploys STJ CKAN downloads immediately for that tribunal's decisions, uses Datajud API for unified metadata across all courts, and initiates formal partnership discussions with TJSP's technical support team. The critical constraint—full text rather than metadata—is only satisfiable for STJ through official channels today. For TJSP, the "Termo de Cooperação" pathway or eventual MNI implementation via eProc migration represents the only compliant approach for a zero-scraping Data Lakehouse.
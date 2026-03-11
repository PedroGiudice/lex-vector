# Prompt engineering e agentes LLM para busca jurídica: estado da arte em 2026

**A separação entre agentes especializados em construção de queries e agentes leitores, combinada com decomposição multi-perspectiva e metadados estruturados como parte ativa da query, constitui o paradigma mais eficaz para RAG jurídico documentado até fevereiro de 2026.** Essa conclusão emerge de uma convergência de papers acadêmicos (LegalMALR, MA-RAG, Stanford Legal Retrieval Benchmark), documentação oficial da Anthropic sobre comportamento de agentes, e implementações em frameworks como LlamaIndex e LangChain. O avanço mais significativo é que a pesquisa deixou de tratar retrieval jurídico como um problema genérico de similaridade semântica — os melhores sistemas hoje decompõem queries por ângulos jurídicos distintos, usam metadados como componente semântico (não filtro), e forçam raciocínio deliberado antes de cada chamada de ferramenta.

---

## 1. Decomposição de queries jurídicas: o LegalMALR e a validação empírica do step-back

A literatura recente documenta três abordagens empiricamente validadas para decompor queries jurídicas complexas, cada uma com trade-offs distintos.

**LegalMALR** (arXiv:2601.17692, janeiro 2025) é o paper mais diretamente relevante. Introduz um Multi-Agent Query Understanding System (MAS) onde agentes especializados — instanciados com Qwen-3-4B-Instruct — reescrevem e decompõem a query original a partir de **perspectivas jurídicas complementares**. Cada reformulação gera uma chamada de retrieval independente; os resultados são mesclados e deduplicados. O sistema usa GRPO (Generalized Reinforcement Policy Optimization) para estabilizar o comportamento estocástico das reescritas. Sobre benchmarks STARD e CSAID (retrieval de estatutos chineses), atinge **HitRate@10 de 0,96**, superando substancialmente baselines RAG convencionais. A contribuição central é demonstrar que queries coloquiais e sub-especificadas escondem múltiplas condições de aplicabilidade estatutária que só emergem com decomposição multi-perspectiva.

Um estudo comparativo direto (Springer, 2025) sobre QA jurídico italiano testou três estratégias de reescrita — multi-query, decomposição e step-back — em domínios de herança e divórcio. **Step-back prompting obteve a melhor acurácia**, provavelmente porque a abstração para princípios jurídicos mais amplos produz queries de retrieval mais eficazes. Esse é o primeiro estudo empírico comparando diretamente essas três estratégias em domínio jurídico.

O paper da COLIEE 2024 (arXiv:2410.12154) documenta outra abordagem: extração de termos jurídicos implícitos via LLM zero-shot, seguida de reformulação orientada ao estilo jurídico. Ambas as técnicas — extração e reformulação — produziram ganhos sobre modelos lexicais e semânticos, superando o melhor time (CAPTAIN) da COLIEE 2023 por 0,3% no F2-score. A reformulação gera "informação de perspectiva diferente" que enriquece queries com conceitos jurídicos implícitos.

O **Stanford Legal Retrieval Benchmark** (Zheng, Guha et al., 2025) traz um insight fundamental: queries jurídicas e passagens-alvo têm **overlap lexical extremamente baixo**, o que explica por que BM25 isolado falha. O paper propõe uma estratégia de expansão de query inspirada no raciocínio jurídico — "generative reasoning rollouts" — que melhora significativamente o recall. A conclusão do paper é que "retrievers precisam ser também raciocinadores jurídicos".

Quanto a **HyDE** e **FLARE**: ambos são amplamente recomendados para domínio jurídico em documentação de frameworks (LlamaIndex, Haystack, Milvus), mas **nenhum paper publicado até março 2026 avalia rigorosamente HyDE ou FLARE em benchmarks jurídicos controlados**. A aplicação conceitual é forte — HyDE geraria um acórdão hipotético cujo embedding captura o espaço semântico de documentos reais — mas a validação empírica é uma lacuna aberta.

---

## 2. Tool descriptions no Claude Code: a dupla natureza das descrições MCP

A pesquisa revela que tool descriptions no MCP são simultaneamente **especificação de software** e **prompt que molda o raciocínio do agente** — uma "superfície de design nova" onde imperfeições textuais se propagam diretamente para erros de comportamento.

O padrão mais documentado pela Anthropic para forçar raciocínio antes de execução é a **"think" tool** — uma ferramenta no-op que serve como scratchpad estruturado entre chamadas de ferramentas. No benchmark τ-bench (domínio aéreo), a think tool combinada com prompt otimizado alcançou **0,570 no pass^1 vs. 0,370 da baseline — melhoria relativa de 54%**. A implementação é simples: uma ferramenta com um único parâmetro `thought` (string), cuja description diz "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log."

A descoberta crítica sobre posicionamento é que **instruções complexas sobre a think tool são mais eficazes no system prompt do que na tool description**. Quando as instruções eram longas ou complexas, colocá-las no system prompt forneceu contexto mais amplo para integrar o raciocínio ao comportamento geral do agente. A Anthropic recomenda explicitamente no system prompt:

> "Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to: list the specific rules that apply, check if all required information is collected, verify that the planned action complies with all policies, iterate over tool results for correctness."

Para **controle de hesitação vs. ação**, a Anthropic documenta dois padrões XML no system prompt: `<default_to_action>` (para agentes mais proativos) e `<do_not_act_before_instructions>` (para agentes que devem pesquisar antes de agir). O segundo é particularmente relevante para RAG jurídico: "Do not jump into implementation... default to providing information, doing research, and providing recommendations rather than taking action."

Um estudo empírico de 103 servidores MCP com 856 ferramentas (arXiv, fevereiro 2025) identificou "tool description smells" — padrões subótimos recorrentes em descriptions que degradam performance do agente. Corrigir esses smells melhorou resultados no benchmark MCP-Universe. As melhores práticas documentadas incluem: nomes claros e intencionais (agentes usam nomes em decisões), docstrings tratadas como prompts, retorno de contexto semântico (resolver UUIDs para nomes significativos), e paginação com defaults sensatos — Claude Code limita respostas de ferramentas a **25.000 tokens**.

A Arcade (fevereiro 2026) codificou **54 padrões** a partir de 8.000+ ferramentas em produção, organizados em 10 categorias. O princípio transversal é: "Design for the LLM, not the human. Tool descriptions, parameter names, and error messages should be optimized for agent comprehension." Outro insight operacional: "A raw 429 means nothing to an LLM. A response that says 'rate limited, retry after 30 seconds or reduce batch size to 50' gives the agent a path forward."

---

## 3. Expansão de queries para RAG jurídico vai muito além de sinônimos

As técnicas mais promissoras para expansão de queries jurídicas operam em três níveis: perspectivas argumentativas, documentos hipotéticos, e taxonomias ontológicas.

**Multi-query com perspectivas jurídicas** é a abordagem mais diretamente implementável. O LangChain MultiQueryRetriever gera 3+ variações da query original por padrão, mas o prompt pode ser customizado para domínio jurídico — por exemplo, "Generate queries from plaintiff, defendant, and judicial perspectives." O RAG Fusion aplica Reciprocal Rank Fusion (RRF) para mesclar resultados: `score(d) = Σ 1/(k + rank_i(d))`. A desvantagem documentada é latência ~1,7x maior que RAG tradicional por causa das chamadas LLM adicionais. O LlamaIndex SubQuestionQueryEngine vai além: decompõe queries complexas em sub-questões direcionadas a índices especializados — constitucional para um, jurisprudencial para outro, estatutário para terceiro.

O **Contextual Retrieval da Anthropic** (setembro 2024) resolve o problema de que chunks isolados perdem contexto. Antes de embeddar cada chunk, Claude gera 50-100 tokens de contexto explicativo situando-o no documento. O resultado: **redução de 35% na taxa de falha de retrieval** com embeddings contextuais isolados, **49%** combinado com BM25 contextual, e **67%** adicionando reranking. O custo é de **$1,02 por milhão de tokens de documento** com prompt caching. Para jurisprudência, o ganho é excepcional porque documentos jurídicos são altamente auto-referenciais: "O tribunal decidiu..." perde significado sem saber qual tribunal, qual caso, qual jurisdição. A Anthropic recomenda prompts customizados por domínio, incluindo glossários de termos definidos em outros documentos.

Para **expansão baseada em ontologias jurídicas**, o projeto LexML Brasil usa CIDOC CRM com W3C SKOS para representar conceitos jurídicos em seis classes (lugar, autoridade, tipo de documento, evento, tipo de conteúdo, idioma), permitindo que múltiplos termos identifiquem os mesmos conceitos — base direta para query expansion. O SAT-Graph RAG (arXiv:2505.00039, 2025) vai mais longe: constrói um Graph RAG ontológico para a Constituição Federal brasileira que modela estrutura hierárquica, evolução temporal (diacrônica) e relações causais entre normas, possibilitando retrieval baseado em conteúdo, propriedades ou conexões entre leis.

O **RFG Framework** (SciTePress, 2025) endereça uma limitação crítica da expansão multi-query padrão: quando o LLM não tem conhecimento suficiente do domínio jurídico específico, as queries expandidas alucinam. O RFG usa pseudo-relevance feedback — recupera documentos iniciais e gera pseudo-queries baseadas na informação recuperada, evitando expansão alucinada.

O **Domain-Partitioned Hybrid RAG** (Goel et al., 2025) para direito indiano demonstra o ganho mais expressivo: um orquestrador agêntico classifica a query, roteia para módulos RAG especializados (case law, estatutos, IPC) e executa retrieval paralelo com fusão de evidências, atingindo **70% de aprovação vs. 37,5% da baseline RAG única**.

---

## 4. Separação entre agente construtor de queries e agente leitor

O padrão de separar "query specialist" de "reader" é amplamente validado e implementável no Claude Code.

O **MA-RAG** (arXiv:2505.20096, maio 2025) formaliza a separação com quatro agentes: Planner (decompõe queries em subtarefas), Step Definer (define passos), Extractor (recupera evidências) e QA Agent (sintetiza respostas). O resultado é que mesmo modelos pequenos como LLaMA3-8B com MA-RAG superam LLMs standalone maiores, demonstrando que a arquitetura importa mais que o tamanho do modelo para retrieval jurídico. O Superlinked VectorHub documenta um padrão similar com "query understanding/parsing agent" separado de "retriever agents" e "reader/orchestrator agents".

No **Claude Code**, subagentes são definidos como arquivos Markdown com YAML frontmatter em `.claude/agents/`, contendo: `name`, `description` (controla quando o subagente é invocado), `tools` (ferramentas acessíveis), e `model`. O campo `description` é essencialmente um prompt que governa a invocação — usar "PROACTIVELY" no description muda se Claude invoca automaticamente ou só quando solicitado. O Task tool permite até **10 tarefas concorrentes**, cada uma com contexto independente de 200k tokens, mas com overhead de ~20k tokens por tarefa. Restrição importante: **subagentes não podem criar seus próprios subagentes** — nesting limitado a um nível.

O **sistema de pesquisa multi-agente da Anthropic** (junho 2025) é o exemplo mais robusto do padrão orchestrator-worker: um agente líder (Claude Opus 4) coordena enquanto spawna subagentes especializados (Claude Sonnet 4) em paralelo. O sistema multi-agente superou Claude Opus 4 single-agent em **90,2%** no eval interno. Token usage explica 80% da variância de performance. Cada subagente precisa de: objetivo claro, formato de output, orientação sobre ferramentas/fontes, e limites de tarefa bem definidos. Sem descrições detalhadas, "agents duplicate work or leave gaps."

Para **loops de reflexão e metacognição**, o padrão Self-RAG (ICLR 2024) treina o LLM para gerar tokens de auto-reflexão que governam estágios do RAG. Após retrieval, o sistema avalia se resultados são relevantes; se irrelevantes, reescreve a query e re-executa — um loop, não um DAG. O LangGraph implementa isso como máquina de estados: Retrieval → Grade Documents → (se irrelevante) Re-write Query → Re-retrieve. O padrão "Auditor Node" (documentado em múltiplos repositórios GitHub) avalia output de ferramentas contra o request original e roteia de volta ao planner se a qualidade for baixa.

---

## 5. Metadados estruturados como componente semântico da query

A técnica mais madura para incorporar metadados na construção da query — e não apenas como filtro pós-busca — é o **Self-Query Retriever** do LangChain, que usa um LLM para decompor uma query em linguagem natural em dois componentes: (a) query semântica para embedding search e (b) filtros estruturados de metadados. Requer definição prévia de `metadata_field_info` (nome, descrição, tipo de cada campo) e uma descrição do conteúdo dos documentos. Para a query "O que o TRF-4 decidiu sobre prescrição intercorrente em 2023?", o sistema geraria: query semântica = "prescrição intercorrente" + filtros = {tribunal = "TRF-4", data >= 2023-01-01, tipo_documento = "acórdão"}.

O **Haystack QueryMetadataExtractor** (maio 2024) segue padrão similar: recebe a query e uma lista de campos de metadados, usa um LLM para extrair valores, e gera filtros estruturados no formato do Haystack. A Amazon Bedrock documenta uma abordagem equivalente usando function calling do LLM para extrair entidades da query e construir filtros dinâmicos.

Para **query routing por tipo de documento**, o padrão documentado mais sólido é o LlamaIndex Router Query Engine: cria-se índices distintos por tipo documental (decisões judiciais, contratos, perícias, legislação), converte-se cada um em query engine com descrição específica, e o router seleciona a engine apropriada baseado na intenção da query. Isso permite construção **fundamentalmente diferenciada** de queries por tipo:

- **Acórdãos**: ênfase em holdings, citações, hierarquia jurisdicional, peso temporal de precedentes
- **Contratos**: foco em identificação de cláusulas, termos definidos, obrigações das partes
- **Perícias**: alvo em descrições metodológicas, conclusões, qualificações do perito
- **Legislação**: retrieval temporal (qual versão vigente), consciência de estrutura hierárquica

O **SAT-Graph API** (arXiv:2510.06002, 2025) introduz um conceito poderoso: "canonical actions" — primitivas atômicas, composáveis e auditáveis para consultar grafos de conhecimento jurídico. Um agente planejador decompõe queries em linguagem natural em DAGs executáveis dessas ações, separando **descoberta probabilística** de **retrieval determinístico**. Suporta busca híbrida combinando semântica, lexical e metadados estruturados, resolução de referências, retrieval de versão point-in-time, e rastreamento causal entre normas.

Para um **schema de metadados** que facilite construção guiada, a combinação ideal para jurisprudência brasileira incluiria: `tipo_documento` (acórdão, contrato, perícia, lei, regulamento), `tribunal` (nome e instância), `data_decisao`, `partes_processuais` (autor, réu, recorrente), `jurisdição` (federal/estadual + vara/câmara), `seção` (ementa, relatório, voto, dispositivo), `tema_jurídico` (usando taxonomia como LexML ou LEXML), e `legislação_citada`. O enrichment contextual (no estilo Anthropic) prepend esses metadados ao chunk antes do embedding, transformando-os em componente semântico permanente.

---

## Conclusão: convergências e lacunas práticas

Três convergências marcam o estado atual. Primeira: **decomposição multi-perspectiva supera reescrita simples** — LegalMALR, MA-RAG e o benchmark de Stanford convergem no achado de que queries jurídicas precisam ser explodidas em ângulos complementares, não apenas parafraseadas. Segunda: **tool descriptions são superfícies de prompt engineering** tão críticas quanto system prompts — a think tool da Anthropic com instruções no system prompt produziu o maior ganho documentado (54%) em raciocínio agêntico, e o estudo empírico de 856 ferramentas MCP confirma que descriptions defeituosas propagam erros sistematicamente. Terceira: **metadados devem entrar na query, não sair como filtro** — o Self-Query Retriever, o Contextual Retrieval e o SAT-Graph API convergem na ideia de que metadados estruturados são componente semântico da busca, não pós-processamento.

As lacunas mais relevantes para implementação são: HyDE não possui validação empírica publicada em benchmarks jurídicos (apesar de forte recomendação conceitual); FLARE também não foi testado especificamente; a decomposição por ângulos como ilícito vs. responsabilidade vs. dispositivo legal vs. contexto contratual — como proposto na query original — não possui paper dedicado, embora o LegalMALR forneça o framework mais próximo; e a integração de ontologias jurídicas brasileiras (LexML) com pipelines RAG agênticos permanece inexplorada, apesar do SAT-Graph ter demonstrado a viabilidade para a Constituição Federal.

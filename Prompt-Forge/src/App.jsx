import React, { useState } from 'react';
import { 
  Sparkles, Copy, Check, Wand2, Sun, Moon,
  ArrowRight, FileCode, Zap, Settings, RefreshCw,
  ChevronDown, Code2, Terminal, FileText, Layers,
  Tag, AlertTriangle, CheckCircle, Info, ChevronUp,
  History, Download, Eye, EyeOff,
  Brackets, FileJson, Hash, List, GitBranch, Scale,
  Cpu, Server
} from 'lucide-react';

const PromptForge = () => {
  const [inputText, setInputText] = useState('');
  const [outputPrompt, setOutputPrompt] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [copied, setCopied] = useState(false);
  const [context, setContext] = useState('general');
  const [detailLevel, setDetailLevel] = useState('balanced');
  const [showSettings, setShowSettings] = useState(true);
  const [showPreview, setShowPreview] = useState(true);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  const [formatOptions, setFormatOptions] = useState({
    useXmlTags: true,
    addContext: true,
    addConstraints: true,
    addOutputFormat: true,
    structuredSteps: true,
    preserveOriginal: true,  // NOVO: preservar texto original
    extractSections: true,   // NOVO: extrair seções automaticamente
    smartReplace: true       // NOVO: substituições contextuais
  });

  const [selectedTags, setSelectedTags] = useState(['tarefa', 'contexto', 'requisitos', 'tecnologias', 'ambiente', 'output']);

  const xmlTagTemplates = [
    { id: 'tarefa', label: 'Tarefa', desc: 'O que deve ser feito (principal)', icon: '🎯' },
    { id: 'background', label: 'Background', desc: 'Contexto/histórico do pedido', icon: '📜' },
    { id: 'contexto', label: 'Contexto', desc: 'Situação atual do projeto', icon: '📋' },
    { id: 'requisitos', label: 'Requisitos', desc: 'O que o usuário pediu explicitamente', icon: '📐' },
    { id: 'restricoes', label: 'Restrições', desc: 'O que NÃO fazer', icon: '🚫' },
    { id: 'tecnologias', label: 'Tecnologias', desc: 'Stack técnico mencionado', icon: '⚙️' },
    { id: 'ambiente', label: 'Ambiente', desc: 'Máquina, RAM, OS, etc.', icon: '💻' },
    { id: 'estrutura', label: 'Estrutura', desc: 'Organização do código', icon: '🏗️' },
    { id: 'output', label: 'Output', desc: 'Formato de saída esperado', icon: '📤' },
    { id: 'validacao', label: 'Validação', desc: 'Como verificar sucesso', icon: '✅' },
    { id: 'arquivos', label: 'Arquivos', desc: 'Files a criar/modificar', icon: '📁' },
    { id: 'pendencias', label: 'Pendências', desc: 'Coisas a resolver depois', icon: '⏳' }
  ];

  const contexts = [
    { id: 'general', label: 'Geral', icon: Code2, desc: 'Desenvolvimento genérico' },
    { id: 'web', label: 'Web Dev', icon: Layers, desc: 'Frontend/Backend web' },
    { id: 'api', label: 'API/Backend', icon: GitBranch, desc: 'APIs e serviços' },
    { id: 'cli', label: 'CLI/Scripts', icon: Terminal, desc: 'Linha de comando' },
    { id: 'automation', label: 'Automação', icon: Zap, desc: 'Scripts e automação' },
    { id: 'refactor', label: 'Refatoração', icon: RefreshCw, desc: 'Melhorar código' },
    { id: 'debug', label: 'Debug', icon: Terminal, desc: 'Corrigir bugs' },
    { id: 'legal', label: 'Legal Tech', icon: Scale, desc: 'Sistemas jurídicos' }
  ];

  const detailLevels = [
    { id: 'minimal', label: 'Mínimo', multiplier: 0.5 },
    { id: 'balanced', label: 'Balanceado', multiplier: 1 },
    { id: 'detailed', label: 'Detalhado', multiplier: 1.5 },
    { id: 'exhaustive', label: 'Exaustivo', multiplier: 2 }
  ];

  // ============ NOVO: Padrões de detecção de seções ============
  const sectionPatterns = {
    tecnologias: [
      /tecnologias?\s*(necessárias?|usadas?|são|serão|:)/i,
      /stack\s*(é|será|:)/i,
      /usar?\s*(as?\s*seguintes?\s*libs?|:)/i,
      /(?:usando|com|baseado em)\s+(\w+(?:\s*,\s*\w+)*)/i
    ],
    ambiente: [
      /(\d+)\s*gb\s*(de\s*)?(ram|memória)/i,
      /wsl2?|ubuntu|windows|linux|macos/i,
      /pc\s*(do\s*)?(trabalho|casa|escritório)/i,
      /máquina\s*(tem|possui|com)/i,
      /rodando\s*(em|no)/i
    ],
    requisitos: [
      /você\s*(deve|deverá|precisa|tem\s*que)/i,
      /é\s*(necessário|preciso|importante|obrigatório)/i,
      /a?\s*única\s*(coisa|opção)/i,
      /confirme\s*que\s*entendeu/i,
      /impreterível|essencial|fundamental/i
    ],
    restricoes: [
      /não\s*(deve|pode|faça|fazer|use)/i,
      /evite|evitar/i,
      /somente|apenas|só/i,
      /exceto|menos/i
    ],
    background: [
      /ontem|antes|anteriormente|já\s*(fizemos|criamos)/i,
      /na\s*verdade|acredito\s*que/i,
      /conflito|problema\s*anterior/i,
      /por\s*ora|depois\s*(nós|iremos|vamos)/i
    ],
    pendencias: [
      /depois\s*(nós|iremos|vamos|resolv)/i,
      /por\s*ora|por\s*enquanto/i,
      /futuramente|no\s*futuro/i,
      /resolver\s*(isso|depois)/i
    ]
  };

  // Termos que NÃO devem ser substituídos quando em contexto válido
  const contextualExceptions = [
    { term: 'isso', validContexts: [/entend\w*\s+isso/i, /confirm\w*\s+isso/i, /fizemos\s+isso/i, /resolver\s+isso/i, /disse\s+isso/i] },
    { term: 'aquilo', validContexts: [/sobre\s+aquilo/i, /falamos\s+aquilo/i] },
    { term: 'coisa', validContexts: [/única\s+coisa/i, /mesma\s+coisa/i, /outra\s+coisa/i] },
    { term: 'algo', validContexts: [/algo\s+(como|tipo|parecido)/i] }
  ];

  // Termos vagos → técnicos (só os que realmente são vagos)
  const vagueToTechnical = {
    'faz aí': 'Implemente',
    'bota': 'Adicione',
    'coloca': 'Insira',
    'dá um jeito': 'Resolva',
    'conserta': 'Corrija',
    'dando pau': 'lançando exceção',
    'bugado': 'com comportamento incorreto',
    'quebrado': 'não funcional',
    'zoado': 'com defeitos',
    'travando': 'causando bloqueio/deadlock',
    'trem': '[componente]',
    'bagulho': '[módulo]',
    'troço': '[componente]',
    'negócio': '[funcionalidade]'
  };

  const techKeywords = {
    'react': 'React', 'vue': 'Vue.js', 'angular': 'Angular', 'next': 'Next.js',
    'svelte': 'Svelte', 'tailwind': 'Tailwind CSS',
    'node': 'Node.js', 'express': 'Express.js', 'fastify': 'Fastify', 'nestjs': 'NestJS',
    'django': 'Django', 'flask': 'Flask', 'fastapi': 'FastAPI',
    'postgres': 'PostgreSQL', 'postgresql': 'PostgreSQL', 'mysql': 'MySQL',
    'mongo': 'MongoDB', 'mongodb': 'MongoDB', 'redis': 'Redis', 'sqlite': 'SQLite',
    'prisma': 'Prisma', 'typeorm': 'TypeORM',
    'python': 'Python', 'typescript': 'TypeScript', 'javascript': 'JavaScript',
    'docker': 'Docker', 'kubernetes': 'Kubernetes',
    'jest': 'Jest', 'vitest': 'Vitest', 'cypress': 'Cypress', 'playwright': 'Playwright',
    'rich': 'Rich (Python)', 'typer': 'Typer (CLI)', 'click': 'Click (CLI)',
    'tesseract': 'Tesseract OCR', 'marker': 'Marker (PDF)',
    'wsl': 'WSL', 'wsl2': 'WSL2', 'ubuntu': 'Ubuntu', 'linux': 'Linux'
  };

  const exampleInputs = [
    "faz um crud de usuários com banco e autenticação",
    "cria uma CLI com rich e typer pra processar PDFs",
    "preciso de um script pra processar pdfs e extrair texto. Estamos no PC do trabalho com 16gb RAM",
    "melhora esse código tá muito bagunçado. A stack é React + TypeScript"
  ];

  const toggleTag = (tagId) => {
    setSelectedTags(prev => 
      prev.includes(tagId) ? prev.filter(t => t !== tagId) : [...prev, tagId]
    );
  };


  // ============ FUNÇÃO PRINCIPAL: Extrair seções do texto ============
  const extractSections = (text) => {
    const sections = {
      background: [],
      tarefa: [],
      requisitos: [],
      restricoes: [],
      tecnologias: [],
      ambiente: [],
      pendencias: [],
      original: text
    };

    // Dividir em parágrafos
    const paragraphs = text.split(/\n\n+/).map(p => p.trim()).filter(p => p);
    
    // Detectar tecnologias explicitamente listadas
    const techListMatch = text.match(/tecnologias?\s*(?:necessárias?|são|:)\s*\n?([\s\S]*?)(?:\n\n|$)/i);
    if (techListMatch) {
      const techLines = techListMatch[1].split('\n').map(l => l.replace(/^[-•*]\s*/, '').trim()).filter(l => l);
      sections.tecnologias = techLines;
    }

    // Detectar ambiente (RAM, WSL, etc)
    const ramMatch = text.match(/(\d+)\s*gb\s*(de\s*)?(ram|memória)/i);
    if (ramMatch) {
      sections.ambiente.push(`${ramMatch[1]}GB de RAM`);
    }
    
    const wslMatch = text.match(/wsl2?|ubuntu|windows\s*\d*/i);
    if (wslMatch) {
      sections.ambiente.push(wslMatch[0].toUpperCase());
    }

    const pcMatch = text.match(/pc\s*(do\s*)?(trabalho|casa|escritório)/i);
    if (pcMatch) {
      sections.ambiente.push(`PC ${pcMatch[2]}`);
    }

    // Classificar parágrafos
    paragraphs.forEach((para, idx) => {
      const lowerPara = para.toLowerCase();
      
      // Background: primeiro parágrafo se fala de passado ou problemas anteriores
      if (idx === 0 && sectionPatterns.background.some(p => p.test(para))) {
        sections.background.push(para);
        return;
      }

      // Pendências: coisas pra resolver depois
      if (sectionPatterns.pendencias.some(p => p.test(para))) {
        sections.pendencias.push(para);
        return;
      }

      // Requisitos explícitos
      if (sectionPatterns.requisitos.some(p => p.test(para))) {
        sections.requisitos.push(para);
        return;
      }

      // Restrições
      if (sectionPatterns.restricoes.some(p => p.test(para)) && para.length < 200) {
        sections.restricoes.push(para);
        return;
      }

      // O resto é tarefa principal
      if (!sectionPatterns.tecnologias.some(p => p.test(para)) && 
          !sections.ambiente.some(a => para.includes(a))) {
        sections.tarefa.push(para);
      }
    });

    // Detectar tecnologias por keywords no texto todo
    const detectedTech = [];
    Object.entries(techKeywords).forEach(([key, value]) => {
      const regex = new RegExp(`\\b${key}\\b`, 'i');
      if (regex.test(text) && !detectedTech.includes(value)) {
        detectedTech.push(value);
      }
    });
    
    // Mesclar tecnologias detectadas com as explícitas
    detectedTech.forEach(tech => {
      if (!sections.tecnologias.some(t => t.toLowerCase().includes(tech.toLowerCase()))) {
        sections.tecnologias.push(tech);
      }
    });

    return sections;
  };

  // ============ Substituição contextual inteligente ============
  const smartReplace = (text) => {
    if (!formatOptions.smartReplace) return text;
    
    let result = text;

    // Verificar exceções contextuais antes de substituir
    Object.entries(vagueToTechnical).forEach(([vague, technical]) => {
      // Verificar se há exceção para este termo
      const exception = contextualExceptions.find(e => e.term === vague);
      
      if (exception) {
        // Verificar se algum contexto válido existe
        const hasValidContext = exception.validContexts.some(pattern => pattern.test(text));
        if (hasValidContext) {
          return; // Não substituir
        }
      }
      
      // Substituir apenas termos isolados (não dentro de palavras)
      const regex = new RegExp(`(?<![\\wáéíóúàèìòùâêîôûãõç])${vague}(?![\\wáéíóúàèìòùâêîôûãõç])`, 'gi');
      result = result.replace(regex, technical);
    });

    return result;
  };

  // ============ Análise do texto ============
  const analyzeInput = (text) => {
    const sections = extractSections(text);
    const issues = [];
    const suggestions = [];

    // Verificar se tem tarefa clara
    if (sections.tarefa.length === 0) {
      issues.push('Não foi possível identificar a tarefa principal');
    }

    // Verificar tecnologias
    if (sections.tecnologias.length === 0) {
      suggestions.push('Nenhuma tecnologia detectada - considere especificar');
    }

    // Verificar termos vagos (apenas os problemáticos)
    const problematicVague = ['troço', 'bagulho', 'negócio', 'trem'];
    problematicVague.forEach(term => {
      if (new RegExp(`\\b${term}\\b`, 'i').test(text)) {
        issues.push(`Termo vago: "${term}" - seja mais específico`);
      }
    });

    // Score baseado na qualidade
    let score = 70;
    score += sections.tarefa.length > 0 ? 10 : -20;
    score += sections.tecnologias.length * 5;
    score += sections.requisitos.length * 5;
    score += sections.ambiente.length * 3;
    score -= issues.length * 10;
    score = Math.max(0, Math.min(100, score));

    return { 
      sections, 
      issues, 
      suggestions, 
      detectedTech: sections.tecnologias,
      score 
    };
  };


  // ============ CONVERSÃO PRINCIPAL ============
  const convertPrompt = () => {
    if (!inputText.trim()) return;
    
    const analysis = analyzeInput(inputText);
    setAnalysisResult(analysis);
    const { sections } = analysis;

    let finalPrompt = '';

    // Processar texto se smartReplace ativo
    const processText = (text) => {
      if (formatOptions.smartReplace) {
        return smartReplace(text);
      }
      return text;
    };

    if (formatOptions.useXmlTags) {
      // ===== BACKGROUND (se existir) =====
      if (selectedTags.includes('background') && sections.background.length > 0) {
        finalPrompt += `<background>\n`;
        sections.background.forEach(p => {
          finalPrompt += `${processText(p)}\n`;
        });
        finalPrompt += `</background>\n\n`;
      }

      // ===== TAREFA PRINCIPAL =====
      if (selectedTags.includes('tarefa')) {
        finalPrompt += `<tarefa>\n`;
        if (sections.tarefa.length > 0) {
          sections.tarefa.forEach(p => {
            finalPrompt += `${processText(p)}\n\n`;
          });
        } else {
          // Se não detectou tarefa, usar texto original processado
          finalPrompt += `${processText(sections.original)}\n`;
        }
        finalPrompt = finalPrompt.trim() + `\n</tarefa>\n\n`;
      }

      // ===== CONTEXTO DO PROJETO =====
      if (selectedTags.includes('contexto') && formatOptions.addContext) {
        const contextInfo = contexts.find(c => c.id === context);
        finalPrompt += `<contexto>\n`;
        finalPrompt += `Tipo: ${contextInfo?.desc || 'Desenvolvimento geral'}\n`;
        finalPrompt += `</contexto>\n\n`;
      }

      // ===== REQUISITOS (extraídos do texto) =====
      if (selectedTags.includes('requisitos') && sections.requisitos.length > 0) {
        finalPrompt += `<requisitos>\n`;
        sections.requisitos.forEach(req => {
          // Limpar e formatar como lista
          const cleanReq = processText(req).replace(/^[-•*]\s*/, '').trim();
          finalPrompt += `- ${cleanReq}\n`;
        });
        finalPrompt += `</requisitos>\n\n`;
      }

      // ===== RESTRIÇÕES (extraídas do texto) =====
      if (selectedTags.includes('restricoes') && sections.restricoes.length > 0) {
        finalPrompt += `<restricoes>\n`;
        sections.restricoes.forEach(rest => {
          const cleanRest = processText(rest).replace(/^[-•*]\s*/, '').trim();
          finalPrompt += `- ${cleanRest}\n`;
        });
        finalPrompt += `</restricoes>\n\n`;
      }

      // ===== TECNOLOGIAS =====
      if (selectedTags.includes('tecnologias') && sections.tecnologias.length > 0) {
        finalPrompt += `<tecnologias>\n`;
        sections.tecnologias.forEach(tech => {
          finalPrompt += `- ${tech}\n`;
        });
        finalPrompt += `</tecnologias>\n\n`;
      }

      // ===== AMBIENTE =====
      if (selectedTags.includes('ambiente') && sections.ambiente.length > 0) {
        finalPrompt += `<ambiente>\n`;
        sections.ambiente.forEach(env => {
          finalPrompt += `- ${env}\n`;
        });
        finalPrompt += `</ambiente>\n\n`;
      }

      // ===== PENDÊNCIAS =====
      if (selectedTags.includes('pendencias') && sections.pendencias.length > 0) {
        finalPrompt += `<pendencias>\n`;
        sections.pendencias.forEach(pend => {
          finalPrompt += `${processText(pend)}\n`;
        });
        finalPrompt += `</pendencias>\n\n`;
      }

      // ===== OUTPUT =====
      if (selectedTags.includes('output') && formatOptions.addOutputFormat) {
        finalPrompt += `<output_esperado>\n`;
        finalPrompt += `- Código funcional e testável\n`;
        finalPrompt += `- Seguir estrutura existente do projeto\n`;
        if (context === 'cli') {
          finalPrompt += `- CLI intuitiva com feedback visual\n`;
        }
        finalPrompt += `</output_esperado>\n`;
      }

    } else {
      // Modo sem XML - Markdown
      if (sections.background.length > 0) {
        finalPrompt += `## Background\n${sections.background.map(processText).join('\n\n')}\n\n`;
      }
      
      finalPrompt += `## Tarefa\n`;
      if (sections.tarefa.length > 0) {
        finalPrompt += sections.tarefa.map(processText).join('\n\n') + '\n\n';
      } else {
        finalPrompt += processText(sections.original) + '\n\n';
      }

      if (sections.requisitos.length > 0) {
        finalPrompt += `## Requisitos\n`;
        sections.requisitos.forEach(r => finalPrompt += `- ${processText(r)}\n`);
        finalPrompt += '\n';
      }

      if (sections.tecnologias.length > 0) {
        finalPrompt += `## Tecnologias\n${sections.tecnologias.map(t => `- ${t}`).join('\n')}\n\n`;
      }

      if (sections.ambiente.length > 0) {
        finalPrompt += `## Ambiente\n${sections.ambiente.map(e => `- ${e}`).join('\n')}\n\n`;
      }
    }

    setOutputPrompt(finalPrompt.trim());
    setHistory(prev => [{ 
      id: Date.now(), 
      input: inputText, 
      output: finalPrompt.trim(), 
      context, 
      timestamp: new Date().toLocaleString('pt-BR') 
    }, ...prev.slice(0, 9)]);
  };


  // ============ Funções auxiliares ============
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(outputPrompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = outputPrompt;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const loadExample = () => {
    setInputText(exampleInputs[Math.floor(Math.random() * exampleInputs.length)]);
    setOutputPrompt('');
    setAnalysisResult(null);
  };

  const exportPrompt = () => {
    const blob = new Blob([outputPrompt], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `prompt-${Date.now()}.txt`;
    a.click();
  };

  const renderFormattedOutput = () => {
    if (!outputPrompt) return null;
    return outputPrompt.split('\n').map((line, i) => {
      // Tags XML de abertura
      if (line.match(/^<[^/][^>]*>$/)) {
        return <div key={i} className={`${isDarkMode ? 'text-cyan-400' : 'text-cyan-600'} font-semibold mt-3`}>{line}</div>;
      }
      // Tags XML de fechamento
      if (line.match(/^<\/[^>]+>$/)) {
        return <div key={i} className={`${isDarkMode ? 'text-cyan-400' : 'text-cyan-600'} font-semibold mb-2`}>{line}</div>;
      }
      // Headers markdown
      if (line.startsWith('##')) {
        return <div key={i} className={`${isDarkMode ? 'text-purple-400' : 'text-purple-600'} font-bold mt-4 mb-1`}>{line}</div>;
      }
      // Listas
      if (line.startsWith('- ') || line.startsWith('├') || line.startsWith('└')) {
        return <div key={i} className={`${isDarkMode ? 'text-green-300' : 'text-green-700'} pl-4`}>{line}</div>;
      }
      // Tipo/Contexto
      if (line.startsWith('Tipo:')) {
        return <div key={i} className={`${isDarkMode ? 'text-yellow-300' : 'text-yellow-700'}`}>{line}</div>;
      }
      // Linha vazia
      if (line.trim() === '') {
        return <div key={i} className="h-1" />;
      }
      // Texto normal
      return <div key={i} className={`${isDarkMode ? 'text-gray-300' : 'text-gray-700'} leading-relaxed`}>{line}</div>;
    });
  };


  // ============ INTERFACE ============
  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDarkMode ? 'bg-gray-950' : 'bg-gray-100'}`}>
      <div className="max-w-7xl mx-auto p-4 md:p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600">
              <Wand2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                Claude Code Prompt Forge
              </h1>
              <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                100% Offline • Extração inteligente de seções
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setShowHistory(!showHistory)} 
              className={`p-2 rounded-lg relative ${isDarkMode ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-200 text-gray-600'}`}
            >
              <History className="w-5 h-5" />
              {history.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-purple-500 rounded-full text-xs text-white flex items-center justify-center">
                  {history.length}
                </span>
              )}
            </button>
            <button 
              onClick={() => setIsDarkMode(!isDarkMode)} 
              className={`p-2 rounded-lg ${isDarkMode ? 'hover:bg-gray-800 text-yellow-400' : 'hover:bg-gray-200 text-gray-700'}`}
            >
              {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* History Panel */}
        {showHistory && history.length > 0 && (
          <div className={`mb-6 p-4 rounded-xl ${isDarkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white border border-gray-200'}`}>
            <div className="flex justify-between items-center mb-3">
              <h3 className={`text-sm font-semibold ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Histórico</h3>
              <button onClick={() => setHistory([])} className="text-xs px-2 py-1 rounded text-red-400 hover:bg-red-900/30">
                Limpar
              </button>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {history.map(item => (
                <button 
                  key={item.id} 
                  onClick={() => { setInputText(item.input); setOutputPrompt(item.output); setShowHistory(false); }}
                  className={`w-full text-left p-3 rounded-lg ${isDarkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-100'}`}
                >
                  <div className="flex justify-between">
                    <span className={`text-sm truncate ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {item.input.substring(0, 60)}...
                    </span>
                    <span className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                      {item.timestamp}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}


        {/* Settings Panel */}
        <div className={`mb-6 rounded-xl overflow-hidden ${isDarkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white border border-gray-200'}`}>
          <button 
            onClick={() => setShowSettings(!showSettings)} 
            className={`w-full p-4 flex items-center justify-between ${isDarkMode ? 'hover:bg-gray-850' : 'hover:bg-gray-50'}`}
          >
            <div className="flex items-center gap-2">
              <Settings className={`w-5 h-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              <span className={`font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Configurações</span>
            </div>
            {showSettings ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </button>
          
          {showSettings && (
            <div className="p-4 pt-0 space-y-6">
              {/* Contexto */}
              <div>
                <label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Contexto do Projeto
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {contexts.map(ctx => (
                    <button 
                      key={ctx.id} 
                      onClick={() => setContext(ctx.id)}
                      className={`p-3 rounded-lg text-left transition-all ${
                        context === ctx.id 
                          ? 'bg-purple-600/20 border-purple-500 border-2' 
                          : isDarkMode ? 'bg-gray-800 border border-gray-700' : 'bg-gray-50 border border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <ctx.icon className={`w-4 h-4 ${context === ctx.id ? 'text-purple-400' : 'text-gray-400'}`} />
                        <span className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{ctx.label}</span>
                      </div>
                      <span className="text-xs text-gray-500">{ctx.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags XML */}
              <div>
                <label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  <div className="flex items-center gap-2"><Tag className="w-4 h-4" />Seções XML a incluir</div>
                </label>
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                  {xmlTagTemplates.map(tag => (
                    <button 
                      key={tag.id} 
                      onClick={() => toggleTag(tag.id)} 
                      title={tag.desc}
                      className={`p-2 rounded-lg text-left transition-all ${
                        selectedTags.includes(tag.id) 
                          ? 'bg-green-600/20 border-green-500 border-2' 
                          : isDarkMode ? 'bg-gray-800 border border-gray-700' : 'bg-gray-50 border border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-1">
                        <span>{tag.icon}</span>
                        <span className={`text-xs font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{tag.label}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Opções de Processamento */}
              <div>
                <label className={`text-sm font-medium mb-2 block ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Processamento
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { key: 'useXmlTags', label: 'Tags XML', icon: Brackets },
                    { key: 'smartReplace', label: 'Substituição Inteligente', icon: Zap },
                    { key: 'extractSections', label: 'Extrair Seções', icon: Layers },
                    { key: 'addOutputFormat', label: 'Output Esperado', icon: FileCode }
                  ].map(opt => (
                    <button 
                      key={opt.key} 
                      onClick={() => setFormatOptions(prev => ({ ...prev, [opt.key]: !prev[opt.key] }))}
                      className={`p-2 rounded-lg flex items-center gap-2 ${
                        formatOptions[opt.key] 
                          ? 'bg-cyan-600/20 border-cyan-500 border' 
                          : isDarkMode ? 'bg-gray-800 border border-gray-700' : 'bg-gray-50 border border-gray-200'
                      }`}
                    >
                      <opt.icon className={`w-4 h-4 ${formatOptions[opt.key] ? 'text-cyan-400' : 'text-gray-500'}`} />
                      <span className={`text-xs ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{opt.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>


        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className={`rounded-xl p-5 ${isDarkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white border border-gray-200'}`}>
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-lg font-semibold flex items-center gap-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                <FileText className="w-5 h-5 text-orange-400" />
                Texto Original
              </h2>
              <div className="flex gap-2">
                <button 
                  onClick={() => { setInputText(''); setOutputPrompt(''); setAnalysisResult(null); }} 
                  className={`px-3 py-1.5 text-sm rounded-lg ${isDarkMode ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
                >
                  Limpar
                </button>
                <button 
                  onClick={loadExample} 
                  className={`px-3 py-1.5 text-sm rounded-lg flex items-center gap-1.5 ${isDarkMode ? 'bg-gray-800 hover:bg-gray-700 text-gray-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
                >
                  <Sparkles className="w-4 h-4" />Exemplo
                </button>
              </div>
            </div>

            <textarea 
              value={inputText} 
              onChange={(e) => { setInputText(e.target.value); setAnalysisResult(null); }}
              placeholder="Cole seu texto aqui...&#10;&#10;O Forge vai detectar automaticamente:&#10;• Tecnologias mencionadas&#10;• Requisitos explícitos&#10;• Informações de ambiente (RAM, OS)&#10;• Tarefas vs Background&#10;• Pendências para depois"
              className={`w-full h-72 p-4 rounded-xl border resize-none focus:outline-none focus:ring-2 ${
                isDarkMode 
                  ? 'bg-gray-950 border-gray-700 text-white placeholder-gray-500 focus:ring-purple-500' 
                  : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:ring-purple-400'
              }`}
            />

            {/* Analysis Results */}
            {analysisResult && (
              <div className={`mt-4 p-4 rounded-xl ${isDarkMode ? 'bg-gray-950 border border-gray-800' : 'bg-gray-50 border border-gray-200'}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    Análise Automática
                  </span>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                    analysisResult.score >= 70 ? 'bg-green-500/20 text-green-400' : 
                    analysisResult.score >= 40 ? 'bg-yellow-500/20 text-yellow-400' : 
                    'bg-red-500/20 text-red-400'
                  }`}>
                    {analysisResult.score}% estruturado
                  </div>
                </div>
                
                {/* Seções detectadas */}
                <div className="flex flex-wrap gap-1 mb-2">
                  {analysisResult.sections.tarefa.length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-900/50 text-purple-300">
                      🎯 Tarefa
                    </span>
                  )}
                  {analysisResult.sections.background.length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-300">
                      📜 Background
                    </span>
                  )}
                  {analysisResult.sections.requisitos.length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/50 text-green-300">
                      📐 Requisitos ({analysisResult.sections.requisitos.length})
                    </span>
                  )}
                  {analysisResult.sections.ambiente.length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-orange-900/50 text-orange-300">
                      💻 Ambiente
                    </span>
                  )}
                  {analysisResult.sections.pendencias.length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-300">
                      ⏳ Pendências
                    </span>
                  )}
                </div>

                {/* Tecnologias */}
                {analysisResult.detectedTech.length > 0 && (
                  <div className="mb-2 flex flex-wrap gap-1">
                    {analysisResult.detectedTech.map((t, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-cyan-900/50 text-cyan-300">
                        ⚙️ {t}
                      </span>
                    ))}
                  </div>
                )}

                {/* Issues */}
                {analysisResult.issues.map((issue, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-red-400 mb-1">
                    <AlertTriangle className="w-3 h-3 mt-0.5" />
                    <span>{issue}</span>
                  </div>
                ))}
                
                {/* Suggestions */}
                {analysisResult.suggestions.map((sug, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-yellow-400 mb-1">
                    <Info className="w-3 h-3 mt-0.5" />
                    <span>{sug}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 flex justify-between items-center">
              <span className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                {inputText.length} caracteres
              </span>
              <button 
                onClick={convertPrompt} 
                disabled={!inputText.trim()}
                className={`px-6 py-2.5 rounded-xl font-medium flex items-center gap-2 ${
                  !inputText.trim() 
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg'
                }`}
              >
                <Wand2 className="w-4 h-4" />
                Forjar Prompt
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>


          {/* Output Panel */}
          <div className={`rounded-xl p-5 ${isDarkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white border border-gray-200'}`}>
            <div className="flex justify-between items-center mb-4">
              <h2 className={`text-lg font-semibold flex items-center gap-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                <Terminal className="w-5 h-5 text-green-400" />
                Prompt Estruturado
              </h2>
              <div className="flex gap-2">
                <button 
                  onClick={() => setShowPreview(!showPreview)} 
                  className={`p-2 rounded-lg ${isDarkMode ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
                  title={showPreview ? 'Ver texto puro' : 'Ver formatado'}
                >
                  {showPreview ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
                <button 
                  onClick={exportPrompt} 
                  disabled={!outputPrompt}
                  className={`p-2 rounded-lg ${!outputPrompt ? 'text-gray-600 cursor-not-allowed' : isDarkMode ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
                  title="Exportar .txt"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button 
                  onClick={copyToClipboard} 
                  disabled={!outputPrompt}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 ${
                    !outputPrompt ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 
                    copied ? 'bg-green-600 text-white' : 
                    isDarkMode ? 'bg-gray-800 hover:bg-gray-700 text-gray-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                  }`}
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copiado!' : 'Copiar'}
                </button>
              </div>
            </div>

            <div className={`h-[28rem] p-4 rounded-xl border overflow-y-auto font-mono text-sm ${
              isDarkMode ? 'bg-gray-950 border-gray-700' : 'bg-gray-50 border-gray-300'
            }`}>
              {outputPrompt ? (
                showPreview ? renderFormattedOutput() : (
                  <pre className={`whitespace-pre-wrap ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    {outputPrompt}
                  </pre>
                )
              ) : (
                <div className={`h-full flex flex-col items-center justify-center ${isDarkMode ? 'text-gray-600' : 'text-gray-400'}`}>
                  <Wand2 className="w-12 h-12 mb-3 opacity-50" />
                  <p className="text-center">
                    Cole seu texto e clique em<br />
                    <span className="font-semibold">"Forjar Prompt"</span>
                  </p>
                  <p className="text-xs mt-2 text-center opacity-70">
                    O Forge detecta seções automaticamente:<br/>
                    tarefa, requisitos, tecnologias, ambiente...
                  </p>
                </div>
              )}
            </div>

            {outputPrompt && (
              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    Pronto para Claude Code
                  </span>
                </div>
                <span className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                  {outputPrompt.length} chars
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tips */}
        <div className={`mt-6 p-4 rounded-xl ${isDarkMode ? 'bg-gray-900/50 border border-gray-800' : 'bg-white/50 border border-gray-200'}`}>
          <h3 className={`text-sm font-semibold mb-2 flex items-center gap-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            <Zap className="w-4 h-4 text-yellow-400" />
            Detecção Automática
          </h3>
          <div className={`grid grid-cols-1 md:grid-cols-4 gap-4 text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            <div className="flex items-start gap-2">
              <span className="text-purple-400 font-bold">🎯</span>
              <span>Separa tarefa principal de background/contexto</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-cyan-400 font-bold">⚙️</span>
              <span>Detecta tecnologias: rich, typer, marker, tesseract...</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-orange-400 font-bold">💻</span>
              <span>Extrai ambiente: RAM, WSL, OS, máquina</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-green-400 font-bold">📐</span>
              <span>Identifica requisitos explícitos do usuário</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptForge;

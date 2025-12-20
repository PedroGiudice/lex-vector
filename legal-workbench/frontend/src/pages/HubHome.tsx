import { Link } from 'react-router-dom';
import { Kanban, FileText, Scale, ArrowRight, FileOutput, Receipt, Bot } from 'lucide-react';

const modules = [
  {
    id: 'trello',
    name: 'Trello Command Center',
    description: 'Gerencie boards, listas e cards do Trello com interface otimizada para produtividade.',
    icon: Kanban,
    color: 'accent-indigo',
    status: 'active'
  },
  {
    id: 'doc-assembler',
    name: 'Doc Assembler',
    description: 'Monte documentos a partir de templates com extração automática de campos.',
    icon: FileText,
    color: 'accent-violet',
    status: 'active'
  },
  {
    id: 'stj',
    name: 'STJ Dados Abertos',
    description: 'Pesquise jurisprudência do Superior Tribunal de Justiça em tempo real.',
    icon: Scale,
    color: 'status-emerald',
    status: 'active'
  },
  {
    id: 'text-extractor',
    name: 'Text Extractor',
    description: 'Extraia texto de PDFs com OCR, filtragem LGPD e suporte a documentos jurídicos.',
    icon: FileOutput,
    color: 'status-emerald',
    status: 'active'
  },
  {
    id: 'ledes-converter',
    name: 'LEDES Converter',
    description: 'Converta faturas DOCX para formato LEDES 1998B para faturamento jurídico.',
    icon: Receipt,
    color: 'accent-amber',
    status: 'active'
  },
  {
    id: 'ccui-assistant',
    name: 'Claude Code',
    description: 'Interface do Claude Code para assistência técnica e desenvolvimento.',
    icon: Bot,
    color: 'ccui-accent',
    status: 'beta'
  },
];

function ModuleCard({ module }: { module: typeof modules[0] }) {
  const Icon = module.icon;

  return (
    <Link
      to={`/${module.id}`}
      className="group block p-6 bg-bg-panel-1 border border-border-default rounded-xl hover:border-accent-indigo/50 transition-all duration-300 hover:bg-bg-panel-2"
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg bg-${module.color}/10`}>
          <Icon className={`text-${module.color}`} size={24} />
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${
          module.status === 'beta'
            ? 'bg-accent-amber/20 text-accent-amber'
            : 'bg-status-emerald/20 text-status-emerald'
        }`}>
          {module.status === 'beta' ? 'Beta' : 'Ativo'}
        </span>
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2 group-hover:text-accent-indigo transition-colors">
        {module.name}
      </h3>
      <p className="text-sm text-text-muted mb-4 line-clamp-2">
        {module.description}
      </p>
      <div className="flex items-center text-sm text-accent-indigo opacity-0 group-hover:opacity-100 transition-opacity">
        <span>Acessar módulo</span>
        <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
      </div>
    </Link>
  );
}

export default function HubHome() {
  return (
    <div className="flex flex-col h-full bg-bg-main">
      {/* Header */}
      <header className="h-16 border-b border-border-default bg-bg-panel-1 flex items-center px-8">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Legal Workbench</h1>
          <p className="text-xs text-text-muted">Hub de ferramentas jurídicas</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto">
          {/* Welcome Section */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-text-primary mb-2">
              Bem-vindo ao Legal Workbench
            </h2>
            <p className="text-text-muted">
              Selecione um módulo abaixo para começar.
            </p>
          </div>

          {/* Module Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {modules.map(module => (
              <ModuleCard key={module.id} module={module} />
            ))}
          </div>

          {/* Stats Section */}
          <div className="mt-12 grid grid-cols-3 gap-4">
            <div className="p-4 bg-bg-panel-1 rounded-lg border border-border-default">
              <p className="text-2xl font-bold text-accent-indigo">6</p>
              <p className="text-sm text-text-muted">Módulos ativos</p>
            </div>
            <div className="p-4 bg-bg-panel-1 rounded-lg border border-border-default">
              <p className="text-2xl font-bold text-accent-violet">v1.0</p>
              <p className="text-sm text-text-muted">Versão atual</p>
            </div>
            <div className="p-4 bg-bg-panel-1 rounded-lg border border-border-default">
              <p className="text-2xl font-bold text-status-emerald">React</p>
              <p className="text-sm text-text-muted">Frontend stack</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

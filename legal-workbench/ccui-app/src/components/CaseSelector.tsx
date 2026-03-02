import { useEffect, useCallback, useState, useRef } from "react";
import { Search } from "lucide-react";
import { useCases } from "../hooks/useCcuiApi";
import { useSession } from "../contexts/SessionContext";
import { useWebSocket } from "../contexts/WebSocketContext";
import { ReactorSpinner } from "./Spinners";
import { ErrorBanner } from "./ErrorBanner";
import type { CaseInfo } from "../types/protocol";

/* -- Helpers -- */

function formatRelativeTime(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 60) return `${mins}min atras`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h atras`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d atras`;
    const weeks = Math.floor(days / 7);
    return `${weeks} sem atras`;
  } catch {
    return iso;
  }
}

type FilterKey = "all" | "active" | "done" | "recent";

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: "all", label: "Todos" },
  { key: "active", label: "Em andamento" },
  { key: "done", label: "Concluidos" },
  { key: "recent", label: "Recentes" },
];

/* -- Sub-components -- */

function StatBlock({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span
        className="text-[24px] leading-none"
        style={{ fontFamily: "var(--font-display)", fontStyle: "italic", color: "var(--text-primary)" }}
      >
        {value}
      </span>
      <span
        className="text-[10px] tracking-[0.12em] uppercase"
        style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}
      >
        {label}
      </span>
    </div>
  );
}

function CaseCard({
  info,
  selected,
  onSelect,
}: {
  info: CaseInfo;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const isReady = info.ready;

  return (
    <button
      onClick={() => isReady && onSelect(info.id)}
      disabled={!isReady}
      aria-disabled={!isReady}
      className="w-full text-left relative group transition-all duration-200 anim-slide-up"
      style={{
        background: "var(--bg-cards)",
        border: selected
          ? "1px solid var(--accent)"
          : "1px solid var(--bg-borders)",
        borderRadius: "var(--radius-md)",
        opacity: isReady ? 1 : 0.4,
        cursor: isReady ? "pointer" : "not-allowed",
      }}
    >
      {/* Accent bar esquerda */}
      {isReady && (
        <span
          className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full transition-opacity duration-200"
          style={{
            background: "var(--accent)",
            opacity: selected ? 1 : 0,
          }}
        />
      )}

      {/* Hover glow bottom */}
      <span
        className="absolute bottom-0 left-4 right-4 h-0.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        style={{ background: "var(--accent)" }}
      />

      <div className="px-4 py-3.5">
        {/* Row 1: Case ID + badge */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <span
            className="text-[13px] font-medium"
            style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}
          >
            {info.id}
          </span>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full"
            style={{
              fontFamily: "var(--font-mono)",
              background: isReady ? "var(--accent-dim)" : "rgba(138, 48, 40, 0.12)",
              color: isReady ? "var(--accent)" : "#8a3028",
              border: `1px solid ${isReady ? "rgba(200,120,74,0.2)" : "rgba(138,48,40,0.2)"}`,
            }}
          >
            {isReady ? "Em andamento" : "Incompleto"}
          </span>
        </div>

        {/* Row 2: Titulo (tipo de acao) */}
        <p
          className="text-[15px] font-medium mb-0.5"
          style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)", lineHeight: "var(--lh-heading)" }}
        >
          {info.title ?? info.id}
        </p>

        {/* Row 3: Partes */}
        {info.parties && (
          <p className="text-[12px] mb-2" style={{ color: "var(--text-secondary)" }}>
            {info.parties}
          </p>
        )}

        {/* Row 4: Tags */}
        {info.tags && info.tags.length > 0 && (
          <div className="flex gap-1.5 mb-3">
            {info.tags.map((tag) => (
              <span
                key={tag}
                className="text-[9px] tracking-[0.08em] px-1.5 py-0.5 rounded-sm"
                style={{
                  fontFamily: "var(--font-mono)",
                  background: "var(--accent-dim)",
                  color: "var(--text-muted)",
                  border: "1px solid rgba(200,120,74,0.1)",
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Divider */}
        <div className="h-px mb-2.5" style={{ background: "var(--bg-borders)" }} />

        {/* Row 5: Docs + progress + tempo */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
              {info.doc_count} docs
            </span>
            <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
              {formatRelativeTime(info.last_modified)}
            </span>
          </div>
          {/* Progress bar */}
          {info.progress !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-[10px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                {info.progress}%
              </span>
              <div
                className="w-[120px] h-1 rounded-full overflow-hidden"
                style={{ background: "var(--bg-borders)" }}
              >
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${info.progress}%`,
                    background: info.progress === 100 ? "var(--agent-oliva)" : "var(--accent)",
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </button>
  );
}

/* -- Main component -- */

export function CaseSelector() {
  const { cases, loading, error, fetchCases } = useCases();
  const { createSession } = useSession();
  const { connect } = useWebSocket();

  const [filter, setFilter] = useState<FilterKey>("all");
  const [search, setSearch] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const filtered = cases.filter((c) => {
    if (filter === "active") return c.ready;
    if (filter === "done") return !c.ready;
    return true;
  }).filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return c.id.toLowerCase().includes(q);
  });

  const handleSelect = useCallback(async (caseId: string) => {
    try {
      await connect();
      createSession(caseId);
    } catch {
      // erro tratado pelo WebSocketContext
    }
  }, [connect, createSession]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // "/" para focar busca
      if (e.key === "/" && document.activeElement !== searchRef.current) {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }
      // Enter para abrir caso selecionado
      if (e.key === "Enter" && document.activeElement !== searchRef.current && filtered.length > 0) {
        const c = filtered[selectedIdx];
        if (c?.ready) handleSelect(c.id);
        return;
      }
      // Arrow keys para navegar
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIdx((prev) => Math.min(prev + 1, filtered.length - 1));
      }
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIdx((prev) => Math.max(prev - 1, 0));
      }
      // Escape para limpar busca
      if (e.key === "Escape") {
        setSearch("");
        searchRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [filtered, selectedIdx, handleSelect]);

  // Reset selection when filter changes
  useEffect(() => {
    setSelectedIdx(0);
  }, [filter, search]);

  // Stats
  const totalCases = cases.length;
  const activeCases = cases.filter((c) => c.ready).length;
  const totalDocs = cases.reduce((sum, c) => sum + c.doc_count, 0);

  return (
    <div
      className="flex flex-col h-screen"
      style={{ background: "var(--bg-base)", color: "var(--text-primary)" }}
    >
      {/* Header */}
      <header
        className="flex items-center justify-between px-12 shrink-0"
        style={{
          height: 56,
          borderBottom: "1px solid var(--bg-borders)",
          background: "var(--bg-header)",
        }}
      >
        <div className="flex items-center gap-1.5">
          <span
            className="text-[20px]"
            style={{ fontFamily: "var(--font-display)", fontStyle: "italic", color: "var(--text-primary)" }}
          >
            Lex Vector
          </span>
          <span className="text-[16px] mx-1" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            /
          </span>
          <span className="text-[13px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
            caso
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            PGR
          </span>
          <div
            className="w-7 h-7 rounded-md flex items-center justify-center text-[12px]"
            style={{
              fontFamily: "var(--font-mono)",
              background: "var(--bg-cards)",
              border: "1px solid var(--bg-borders)",
              color: "var(--text-secondary)",
            }}
          >
            P
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto px-12 pt-10 pb-4 anim-fade-in">
        <div className="max-w-[1184px]">
          {/* Title */}
          <h1
            className="text-[32px] mb-1"
            style={{ fontFamily: "var(--font-display)", fontStyle: "italic", color: "var(--text-primary)", lineHeight: "var(--lh-heading)" }}
          >
            Selecione um caso
          </h1>
          <p className="text-[14px] mb-8" style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
            para iniciar a sessao de trabalho
          </p>

          {/* Search + Filters */}
          <div className="flex items-center gap-4 mb-8">
            <div
              className="relative flex-none"
              style={{ width: 500 }}
            >
              <Search
                className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4"
                style={{ color: "var(--text-muted)" }}
              />
              <input
                ref={searchRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por numero, parte ou assunto..."
                className="w-full pl-10 pr-4 py-2.5 text-[13px] outline-none transition-colors"
                style={{
                  fontFamily: "var(--font-mono)",
                  background: "var(--bg-panels)",
                  border: "1px solid var(--bg-borders)",
                  borderRadius: "var(--radius-lg)",
                  color: "var(--text-primary)",
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "var(--bg-borders)")}
              />
            </div>

            <div className="flex gap-1.5">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className="px-3 py-1.5 text-[11px] tracking-[0.04em] transition-all duration-150"
                  style={{
                    fontFamily: "var(--font-mono)",
                    borderRadius: "var(--radius-md)",
                    background: filter === f.key ? "var(--bg-cards)" : "transparent",
                    border: filter === f.key ? "1px solid var(--bg-borders)" : "1px solid transparent",
                    color: filter === f.key ? "var(--text-primary)" : "var(--text-muted)",
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Stats row */}
          <div
            className="flex gap-[200px] py-4 mb-6"
            style={{ borderTop: "1px solid var(--bg-borders)", borderBottom: "1px solid var(--bg-borders)" }}
          >
            <StatBlock value={String(totalCases)} label="TOTAL" />
            <StatBlock value={String(activeCases)} label="EM ANDAMENTO" />
            <StatBlock value={String(totalDocs)} label="DOCUMENTOS" />
            <StatBlock value="--" label="ULTIMA ATIVIDADE" />
          </div>

          {/* Section label */}
          <p
            className="text-[10px] tracking-[0.12em] uppercase mb-4"
            style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}
          >
            CASOS RECENTES
          </p>

          {/* Loading */}
          {loading && (
            <div className="flex flex-col items-center gap-5 py-20">
              <ReactorSpinner className="w-[80px] h-[80px]" />
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Buscando casos...
              </span>
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <ErrorBanner type="server" message={error} onRetry={fetchCases} />
          )}

          {/* Empty */}
          {!loading && !error && filtered.length === 0 && (
            <div
              className="flex flex-col items-center gap-3 py-20 rounded-lg"
              style={{ border: "1px solid var(--bg-borders)", color: "var(--text-secondary)" }}
            >
              <p className="text-sm">Nenhum caso encontrado.</p>
              <button
                onClick={fetchCases}
                className="text-xs hover:underline underline-offset-2"
                style={{ color: "var(--accent)" }}
              >
                Tentar novamente
              </button>
            </div>
          )}

          {/* Cards grid */}
          {!loading && !error && filtered.length > 0 && (
            <div className="grid grid-cols-3 gap-5 anim-stagger">
              {filtered.map((c, idx) => (
                <CaseCard
                  key={c.id}
                  info={c}
                  selected={idx === selectedIdx}
                  onSelect={handleSelect}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer
        className="shrink-0 flex items-center justify-between px-12"
        style={{
          height: 56,
          borderTop: "1px solid var(--bg-borders)",
          background: "var(--bg-header)",
        }}
      >
        <div className="flex gap-2">
          <button
            className="flex items-center gap-1.5 px-4 py-2 text-[11px] tracking-[0.08em] uppercase transition-colors"
            style={{
              fontFamily: "var(--font-mono)",
              border: "1px solid var(--bg-borders)",
              borderRadius: "var(--radius-lg)",
              color: "var(--text-secondary)",
              background: "transparent",
            }}
          >
            + NOVO CASO
          </button>
          <button
            className="flex items-center gap-1.5 px-4 py-2 text-[11px] tracking-[0.08em] uppercase transition-colors"
            style={{
              fontFamily: "var(--font-mono)",
              border: "1px solid var(--bg-borders)",
              borderRadius: "var(--radius-lg)",
              color: "var(--text-secondary)",
              background: "transparent",
            }}
          >
            IMPORTAR
          </button>
        </div>
        <div className="flex gap-6">
          <KbdHint keys="Enter" label="abrir caso" />
          <KbdHint keys="N" label="novo caso" />
          <KbdHint keys="/" label="buscar" />
          <KbdHint keys="?" label="atalhos" />
        </div>
      </footer>
    </div>
  );
}

function KbdHint({ keys, label }: { keys: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-[10px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
      <kbd
        className="px-1 py-0.5 rounded text-[9px]"
        style={{ background: "var(--bg-cards)", border: "1px solid var(--bg-borders)", color: "var(--text-secondary)" }}
      >
        {keys}
      </kbd>
      {label}
    </span>
  );
}

export default CaseSelector;

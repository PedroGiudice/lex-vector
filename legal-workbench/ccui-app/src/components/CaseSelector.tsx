import { useEffect } from "react";
import { FolderOpen, CheckCircle, AlertCircle, FileText, Calendar } from "lucide-react";
import { useCases } from "../hooks/useCcuiApi";
import { useSession } from "../contexts/SessionContext";
import { useWebSocket } from "../contexts/WebSocketContext";
import { ReactorSpinner } from "./Spinners";
import { ErrorBanner } from "./ErrorBanner";
import type { CaseInfo } from "../types/protocol";

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function CaseCard({ info, onSelect }: { info: CaseInfo; onSelect: (id: string) => void }) {
  const isReady = info.ready;

  return (
    <button
      onClick={() => isReady && onSelect(info.id)}
      disabled={!isReady}
      aria-disabled={!isReady}
      className={[
        "w-full text-left rounded-xl border transition-all duration-200 anim-slide-up",
        "group relative overflow-hidden",
        isReady
          ? [
              "border-[var(--border)] bg-[var(--bg-surface)]",
              "hover:border-[var(--accent)] hover:bg-[var(--accent-hover)]",
              "cursor-pointer",
            ].join(" ")
          : "border-[var(--border)] bg-[var(--bg-surface)] opacity-40 cursor-not-allowed",
      ].join(" ")}
    >
      {/* Linha de destaque lateral ao hover */}
      {isReady && (
        <span
          className="absolute left-0 top-3 bottom-3 w-0.5 rounded-full bg-[var(--accent)]
                     opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        />
      )}

      <div className="px-5 py-4">
        {/* Linha principal: nome + badge */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <FolderOpen
              className="w-4 h-4 shrink-0 transition-colors duration-200"
              style={{ color: isReady ? "var(--accent)" : "var(--text-muted)" }}
            />
            <span
              className="text-sm font-medium text-[var(--text-primary)] truncate"
              title={info.id}
            >
              {info.id}
            </span>
          </div>

          <span
            className={[
              "flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border shrink-0",
              isReady
                ? "text-emerald-400 border-emerald-500/20 bg-emerald-500/8"
                : "text-rose-400 border-rose-500/20 bg-rose-500/8",
            ].join(" ")}
          >
            {isReady ? (
              <CheckCircle className="w-3 h-3" />
            ) : (
              <AlertCircle className="w-3 h-3" />
            )}
            {isReady ? "Pronto" : "Incompleto"}
          </span>
        </div>

        {/* Linha secundaria: metadados */}
        <div className="mt-2.5 flex items-center gap-5 text-[12px] text-[var(--text-secondary)]">
          <span className="flex items-center gap-1.5">
            <FileText className="w-3 h-3" />
            {info.doc_count} {info.doc_count === 1 ? "doc" : "docs"}
          </span>
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3 h-3" />
            {formatDate(info.last_modified)}
          </span>
        </div>
      </div>
    </button>
  );
}

export function CaseSelector() {
  const { cases, loading, error, fetchCases } = useCases();
  const { createSession } = useSession();
  const { connect } = useWebSocket();

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const handleSelect = async (caseId: string) => {
    try {
      await connect();
      createSession(caseId);
    } catch {
      // erro de conexao ja tratado pelo status do WebSocketContext
    }
  };

  const readyCases = cases.filter((c) => c.ready);
  const notReadyCases = cases.filter((c) => !c.ready);

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: "var(--bg-base)", color: "var(--text-primary)" }}
    >
      {/* Header */}
      <header
        className="flex items-center px-8 py-4 border-b shrink-0"
        style={{ borderColor: "var(--border)", background: "var(--bg-surface)" }}
      >
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-semibold tracking-[0.12em] uppercase"
            style={{ color: "var(--accent)" }}
          >
            LexVector
          </span>
          <span className="text-[var(--text-muted)]">/</span>
          <span className="text-xs text-[var(--text-secondary)]">Selecionar caso</span>
        </div>
      </header>

      {/* Corpo */}
      <main className="flex-1 flex flex-col items-center justify-start px-6 py-14 anim-fade-in">
        <div className="w-full max-w-[560px]">

          {/* Titulo */}
          <div className="mb-9">
            <h1 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
              Casos disponíveis
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Selecione um caso para iniciar o assistente jurídico.
            </p>
          </div>

          {/* Estado: carregando */}
          {loading && (
            <div className="flex flex-col items-center gap-5 py-20">
              <ReactorSpinner className="w-[80px] h-[80px]" />
              <span className="text-sm text-[var(--text-secondary)]">
                Buscando casos...
              </span>
            </div>
          )}

          {/* Estado: erro */}
          {!loading && error && (
            <ErrorBanner
              type="server"
              message={error}
              onRetry={fetchCases}
            />
          )}

          {/* Estado: vazio */}
          {!loading && !error && cases.length === 0 && (
            <div
              className="flex flex-col items-center gap-3 py-20 rounded-xl border"
              style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
            >
              <FolderOpen className="w-8 h-8 opacity-30" />
              <p className="text-sm">Nenhum caso encontrado.</p>
              <p className="text-xs text-[var(--text-muted)]">
                Verifique a conexao com o backend (porta 8005).
              </p>
              <button
                onClick={fetchCases}
                className="mt-2 text-xs text-[var(--accent)] hover:underline underline-offset-2 transition-opacity duration-150"
              >
                Tentar novamente
              </button>
            </div>
          )}

          {/* Lista de casos prontos */}
          {!loading && !error && readyCases.length > 0 && (
            <ul className="space-y-2.5 anim-stagger">
              {readyCases.map((c) => (
                <li key={c.id}>
                  <CaseCard info={c} onSelect={handleSelect} />
                </li>
              ))}
            </ul>
          )}

          {/* Casos incompletos (separados visualmente) */}
          {!loading && !error && notReadyCases.length > 0 && (
            <div className="mt-8">
              <p className="text-[11px] font-medium tracking-[0.08em] uppercase text-[var(--text-muted)] mb-3">
                Incompletos
              </p>
              <ul className="space-y-2 anim-stagger">
                {notReadyCases.map((c) => (
                  <li key={c.id}>
                    <CaseCard info={c} onSelect={handleSelect} />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default CaseSelector;

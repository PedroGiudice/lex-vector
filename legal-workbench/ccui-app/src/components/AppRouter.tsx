import { useState, useEffect, useRef } from "react";
import { useSession } from "../contexts/SessionContext";
import { CaseSelector } from "./CaseSelector";
import { SessionView } from "./SessionView";

/**
 * Roteamento por estado com crossfade de 200ms entre telas.
 * Sem react-router -- fluxo linear de uma unica janela.
 */
export function AppRouter() {
  const { sessionId, reset } = useSession();
  const hasSession = !!sessionId;

  // Controla qual tela esta visivel e qual esta saindo
  const [displayState, setDisplayState] = useState<"case" | "session">(
    hasSession ? "session" : "case"
  );
  const [isTransitioning, setIsTransitioning] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    const target = hasSession ? "session" : "case";
    if (target === displayState) return;

    // Inicia transicao: fade-out da tela atual
    setIsTransitioning(true);

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setDisplayState(target);
      setIsTransitioning(false);
    }, 200);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [hasSession, displayState]);

  return (
    <div
      className="h-screen w-screen"
      style={{
        opacity: isTransitioning ? 0 : 1,
        transition: "opacity 200ms ease",
      }}
    >
      {displayState === "session" ? (
        <SessionView onClose={reset} />
      ) : (
        <CaseSelector />
      )}
    </div>
  );
}

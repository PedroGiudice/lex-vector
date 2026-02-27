import { useSession } from "../contexts/SessionContext";
import { CaseSelector } from "./CaseSelector";
import { SessionView } from "./SessionView";

/**
 * Roteamento por estado: sem sessao ativa -> CaseSelector, com sessao -> SessionView.
 * Nao usa react-router -- fluxo linear de uma unica janela.
 */
export function AppRouter() {
  const { sessionId, reset } = useSession();

  if (sessionId) {
    return <SessionView onClose={reset} />;
  }

  return <CaseSelector />;
}

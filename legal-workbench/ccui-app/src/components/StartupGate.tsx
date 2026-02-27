import { useState, useEffect, useCallback, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";
import { ErrorBanner } from "./ErrorBanner";
import { ReactorSpinner } from "./Spinners";

type Phase =
  | "checking"
  | "generating-key"
  | "show-pubkey"
  | "opening-tunnel"
  | "waiting-health"
  | "ready"
  | "error";

interface Props {
  children: ReactNode;
}

export function StartupGate({ children }: Props) {
  const [phase, setPhase] = useState<Phase>("checking");
  const [pubKey, setPubKey] = useState("");
  const [error, setError] = useState("");
  const [healthAttempt, setHealthAttempt] = useState(0);

  const MAX_HEALTH_ATTEMPTS = 15;
  const HEALTH_INTERVAL_MS = 2000;

  const startup = useCallback(async () => {
    setPhase("checking");
    setError("");

    try {
      // 1. Verificar se keypair existe
      const hasKey: boolean = await invoke("check_keypair_exists");

      if (!hasKey) {
        // Primeira execucao: gerar keypair
        setPhase("generating-key");
        const key: string = await invoke("generate_keypair");
        setPubKey(key);
        setPhase("show-pubkey");
        return; // Para aqui -- usuario precisa registrar a chave na VM
      }

      // 2. Abrir tunnel SSH
      setPhase("opening-tunnel");
      const config: { vm_host: string; local_port: number } =
        await invoke("get_config");
      await invoke("open_tunnel", { host: config.vm_host });

      // 3. Aguardar health check (tunnel pode demorar para estabelecer)
      setPhase("waiting-health");
      setHealthAttempt(0);
    } catch (err) {
      setError(String(err));
      setPhase("error");
    }
  }, []);

  // Health check polling apos abrir tunnel
  useEffect(() => {
    if (phase !== "waiting-health") return;

    const interval = setInterval(async () => {
      try {
        const healthy: boolean = await invoke("check_health");
        if (healthy) {
          clearInterval(interval);
          setPhase("ready");
          return;
        }
      } catch {
        // Ignorar erros de health check durante espera
      }

      setHealthAttempt((prev) => {
        const next = prev + 1;
        if (next >= MAX_HEALTH_ATTEMPTS) {
          clearInterval(interval);
          setError(
            `Backend nao respondeu apos ${MAX_HEALTH_ATTEMPTS} tentativas. Verifique se o ccui-backend esta rodando na VM.`
          );
          setPhase("error");
        }
        return next;
      });
    }, HEALTH_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [phase]);

  // Iniciar no mount
  useEffect(() => {
    startup();
  }, [startup]);

  // Callback para apos registrar a pub key
  const handleKeyRegistered = useCallback(() => {
    // Continuar startup: abrir tunnel
    setPhase("checking");
    startup();
  }, [startup]);

  const handleCopyKey = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(pubKey);
    } catch {
      // Fallback: selecionar texto manualmente
    }
  }, [pubKey]);

  // Fase "ready": renderiza o app
  if (phase === "ready") {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg-base)" }}>
      <div className="max-w-lg w-full mx-4 p-8 rounded-xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>

        {phase === "checking" && (
          <div className="flex flex-col items-center gap-4">
            <ReactorSpinner className="w-16 h-16" />
            <p style={{ color: "var(--text-secondary)" }}>Verificando configuracao...</p>
          </div>
        )}

        {phase === "generating-key" && (
          <div className="flex flex-col items-center gap-4">
            <ReactorSpinner className="w-16 h-16" />
            <p style={{ color: "var(--text-secondary)" }}>Gerando par de chaves ED25519...</p>
          </div>
        )}

        {phase === "show-pubkey" && (
          <div className="flex flex-col gap-5">
            <h2 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
              Primeira execucao
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Um par de chaves ED25519 foi gerado em <code className="px-1.5 py-0.5 rounded text-xs" style={{ background: "var(--bg-input)", color: "var(--accent)" }}>~/.ccui/</code>.
              Para conectar ao backend, registre a chave publica abaixo na VM:
            </p>

            <div className="relative">
              <pre
                className="p-4 rounded-lg text-xs break-all whitespace-pre-wrap select-all"
                style={{ background: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border)" }}
              >
                {pubKey}
              </pre>
              <button
                onClick={handleCopyKey}
                className="absolute top-2 right-2 px-2 py-1 rounded text-xs transition-colors"
                style={{ background: "var(--bg-elevated)", color: "var(--text-muted)", border: "1px solid var(--border)" }}
              >
                Copiar
              </button>
            </div>

            <div className="p-3 rounded-lg text-xs leading-relaxed" style={{ background: "var(--bg-input)", color: "var(--text-muted)" }}>
              <p className="font-medium mb-1" style={{ color: "var(--text-secondary)" }}>Na VM, execute:</p>
              <code className="block" style={{ color: "var(--accent)" }}>
                echo "CHAVE_ACIMA" &gt;&gt; ~/.ssh/authorized_keys
              </code>
            </div>

            <button
              onClick={handleKeyRegistered}
              className="w-full py-3 rounded-lg font-medium text-sm transition-colors"
              style={{ background: "var(--accent)", color: "#fff" }}
            >
              Ja registrei a chave -- continuar
            </button>
          </div>
        )}

        {phase === "opening-tunnel" && (
          <div className="flex flex-col items-center gap-4">
            <ReactorSpinner className="w-16 h-16" />
            <p style={{ color: "var(--text-secondary)" }}>Abrindo tunnel SSH...</p>
          </div>
        )}

        {phase === "waiting-health" && (
          <div className="flex flex-col items-center gap-4">
            <ReactorSpinner className="w-16 h-16" />
            <p style={{ color: "var(--text-secondary)" }}>
              Conectando ao backend... ({healthAttempt}/{MAX_HEALTH_ATTEMPTS})
            </p>
          </div>
        )}

        {phase === "error" && (
          <div className="flex flex-col gap-4">
            <ErrorBanner type="connection" message={error} onRetry={startup} />
          </div>
        )}
      </div>
    </div>
  );
}

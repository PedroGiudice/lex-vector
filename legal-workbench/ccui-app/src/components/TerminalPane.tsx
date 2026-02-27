import React, { useEffect, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";
import { useWebSocket } from "../contexts/WebSocketContext";

interface TerminalPaneProps {
  channel: string;
}

export const TerminalPane: React.FC<TerminalPaneProps> = ({ channel }) => {
  const { onMessage } = useWebSocket();
  const termRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);

  useEffect(() => {
    if (!termRef.current) return;

    const term = new Terminal({
      theme: {
        background: "#1a1a1a",
        foreground: "#e0e0e0",
        cursor: "#d97757",
        selectionBackground: "#d9775733",
      },
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      fontSize: 13,
      lineHeight: 1.5,
      cursorBlink: false,
      cursorStyle: "underline",
      disableStdin: true,
      scrollback: 5000,
      convertEol: true,
    });

    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(termRef.current);
    fit.fit();

    xtermRef.current = term;
    fitRef.current = fit;

    const ro = new ResizeObserver(() => {
      try {
        fit.fit();
      } catch {}
    });
    ro.observe(termRef.current);

    return () => {
      ro.disconnect();
      term.dispose();
      xtermRef.current = null;
      fitRef.current = null;
    };
  }, []);

  useEffect(() => {
    xtermRef.current?.clear();
  }, [channel]);

  useEffect(() => {
    return onMessage((msg) => {
      if (msg.type === "output" && msg.channel === channel) {
        xtermRef.current?.write(msg.data);
      }
    });
  }, [onMessage, channel]);

  return (
    <div
      ref={termRef}
      className="h-full w-full"
      aria-label={`Saida do canal ${channel}`}
      style={{ background: "#1a1a1a" }}
    />
  );
};

export default TerminalPane;

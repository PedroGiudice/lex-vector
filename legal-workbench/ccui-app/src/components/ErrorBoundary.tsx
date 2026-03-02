import { Component } from "react";
import type { ReactNode, ErrorInfo } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("[ErrorBoundary]", error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            background: "var(--bg-base)",
            gap: "16px",
            padding: "24px",
          }}
        >
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontStyle: "italic",
              fontSize: "24px",
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Erro inesperado
          </h1>

          <p
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "12px",
              color: "var(--text-muted)",
              maxWidth: "500px",
              textAlign: "center",
              margin: 0,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {this.state.error?.message}
          </p>

          <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                padding: "8px 16px",
                borderRadius: "var(--radius-md)",
                border: "none",
                background: "var(--accent)",
                color: "var(--bg-base)",
                cursor: "pointer",
              }}
            >
              Recarregar
            </button>
            <button
              onClick={this.handleReset}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                padding: "8px 16px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--bg-borders)",
                background: "var(--bg-cards)",
                color: "var(--text-secondary)",
                cursor: "pointer",
              }}
            >
              Tentar novamente
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

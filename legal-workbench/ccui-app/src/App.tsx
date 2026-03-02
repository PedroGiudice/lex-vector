import { ErrorBoundary } from "./components/ErrorBoundary";
import { WebSocketProvider } from "./contexts/WebSocketContext";
import { SessionProvider } from "./contexts/SessionContext";
import { StartupGate } from "./components/StartupGate";
import { AppRouter } from "./components/AppRouter";

function App() {
  return (
    <ErrorBoundary>
      <StartupGate>
        <WebSocketProvider>
          <SessionProvider>
            <AppRouter />
          </SessionProvider>
        </WebSocketProvider>
      </StartupGate>
    </ErrorBoundary>
  );
}

export default App;

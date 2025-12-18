"""
QA Commander - Agente de Testes E2E

Este agente utiliza o Chrome DevTools via MCP para realizar testes de interface
de forma autônoma, validando o estado visual contra o código React.

Requisitos:
  pip install google-adk mcp nest_asyncio
  npx chrome-devtools-mcp (instalado automaticamente via npx)

Uso:
  python -m qa_commander.agent "Teste o Trello Command Center"

  Ou via run_agent.py:
  python run_agent.py qa_commander --prompt "Navegue para http://localhost/app e liste os boards"
"""
import asyncio
import json
import os
import sys
import base64
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

# Fix para rodar dentro de outro event loop (ADK Runner)
import nest_asyncio
nest_asyncio.apply()

# Adiciona shared ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool

# Importa config compartilhada
from shared.config import Config

# --- CONFIGURAÇÃO ---
PROJECT_ROOT = Path("/home/cmr-auto/claude-work/repos/Claude-Code-Projetos")
SCREENSHOT_DIR = PROJECT_ROOT / "adk-agents" / "qa_commander" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Modelo para o agente (usar 2.5 Flash para melhor suporte a tools)
MODEL_NAME = Config.MODELS.GEMINI_25_FLASH


# --- PONTE CHROME MCP (Bridge Síncrona) ---
class ChromeBridge:
    """
    Bridge síncrona para o Chrome DevTools MCP.
    Permite chamar funções async do MCP de dentro de tools síncronas do ADK.
    """

    def __init__(self):
        self.session = None
        self._stdio_context = None
        self._loop = None
        self._connected = False

    def _ensure_loop(self):
        """Garante que temos um event loop."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    async def _connect_async(self):
        """Conecta ao servidor MCP do Chrome DevTools."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command="npx",
            args=["chrome-devtools-mcp", "--headless", "--isolated"],  # Headless + isolated profile
            env=None
        )

        self._stdio_context = stdio_client(server_params)
        read, write = await self._stdio_context.__aenter__()

        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()
        self._connected = True

        # Lista tools disponíveis
        tools = await self.session.list_tools()
        print(f"[ChromeBridge] Conectado! {len(tools.tools)} ferramentas disponíveis.")
        return self

    async def _disconnect_async(self):
        """Desconecta do servidor MCP."""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
        except:
            pass
        try:
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
        except:
            pass
        self._connected = False

    def connect(self):
        """Conecta de forma síncrona."""
        loop = self._ensure_loop()
        loop.run_until_complete(self._connect_async())

    def disconnect(self):
        """Desconecta de forma síncrona."""
        if self._loop and not self._loop.is_closed():
            self._loop.run_until_complete(self._disconnect_async())

    def call_tool(self, tool_name: str, args: dict = None) -> Any:
        """Executa uma ferramenta MCP de forma síncrona."""
        if not self._connected:
            self.connect()

        async def _call():
            return await self.session.call_tool(tool_name, arguments=args or {})

        loop = self._ensure_loop()
        return loop.run_until_complete(_call())

    def extract_result(self, result) -> str:
        """Extrai texto do resultado MCP."""
        if result.content:
            texts = []
            for content in result.content:
                if hasattr(content, 'text'):
                    texts.append(content.text)
            return "\n".join(texts) if texts else "OK"
        return "OK (sem output)"


# Instância global (singleton)
bridge = ChromeBridge()


# --- FERRAMENTAS DO AGENTE ---

def chrome_navigate(url: str) -> str:
    """
    Navega o browser para uma URL.

    Args:
        url: URL completa (ex: http://localhost/app, https://google.com)

    Returns:
        Status da navegação
    """
    try:
        result = bridge.call_tool("navigate_page", {"url": url, "type": "url"})
        return f"✓ Navegado para {url}"
    except Exception as e:
        return f"✗ Erro ao navegar: {str(e)}"


def chrome_snapshot() -> str:
    """
    Captura o estado atual da página (DOM acessível).
    Retorna uma representação textual dos elementos visíveis.

    Returns:
        Snapshot do DOM com elementos interativos
    """
    try:
        result = bridge.call_tool("take_snapshot", {})
        return bridge.extract_result(result)
    except Exception as e:
        return f"✗ Erro ao capturar snapshot: {str(e)}"


def chrome_click(uid: str) -> str:
    """
    Clica em um elemento pelo seu UID (obtido do snapshot).

    Args:
        uid: ID único do elemento (ex: "e15", "button-submit")

    Returns:
        Resultado do clique
    """
    try:
        result = bridge.call_tool("click", {"uid": uid})
        return f"✓ Clicado em elemento {uid}"
    except Exception as e:
        return f"✗ Erro ao clicar: {str(e)}"


def chrome_fill(uid: str, value: str) -> str:
    """
    Preenche um campo de input com um valor.

    Args:
        uid: ID único do elemento input
        value: Valor a preencher

    Returns:
        Resultado do preenchimento
    """
    try:
        result = bridge.call_tool("fill", {"uid": uid, "value": value})
        return f"✓ Preenchido '{value}' em {uid}"
    except Exception as e:
        return f"✗ Erro ao preencher: {str(e)}"


def chrome_screenshot(name: str) -> str:
    """
    Salva um screenshot da página atual.

    Args:
        name: Nome do arquivo (sem extensão)

    Returns:
        Caminho do arquivo salvo
    """
    try:
        result = bridge.call_tool("take_screenshot", {})

        # O resultado pode ter a imagem em diferentes formatos
        if result.content:
            for content in result.content:
                if hasattr(content, 'data'):
                    # Base64 encoded
                    safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{safe_name}_{timestamp}.png"
                    path = SCREENSHOT_DIR / filename

                    with open(path, "wb") as f:
                        f.write(base64.b64decode(content.data))
                    return f"✓ Screenshot salvo: {path}"

        return "Screenshot capturado (formato não suportado para salvar)"
    except Exception as e:
        return f"✗ Erro ao capturar screenshot: {str(e)}"


def chrome_list_pages() -> str:
    """
    Lista todas as páginas/abas abertas no browser.

    Returns:
        Lista de páginas com seus índices
    """
    try:
        result = bridge.call_tool("list_pages", {})
        return bridge.extract_result(result)
    except Exception as e:
        return f"✗ Erro ao listar páginas: {str(e)}"


def chrome_select_page(page_idx: int) -> str:
    """
    Seleciona uma página/aba pelo índice.

    Args:
        page_idx: Índice da página (0-based)

    Returns:
        Confirmação da seleção
    """
    try:
        result = bridge.call_tool("select_page", {"pageIdx": page_idx})
        return f"✓ Página {page_idx} selecionada"
    except Exception as e:
        return f"✗ Erro ao selecionar página: {str(e)}"


def chrome_evaluate(js_code: str) -> str:
    """
    Executa JavaScript na página e retorna o resultado.

    Args:
        js_code: Código JavaScript a executar

    Returns:
        Resultado da execução
    """
    try:
        result = bridge.call_tool("evaluate_script", {"function": js_code})
        return bridge.extract_result(result)
    except Exception as e:
        return f"✗ Erro ao executar JS: {str(e)}"


def read_file(file_path: str) -> str:
    """
    Lê o código fonte de um arquivo para validação.

    Args:
        file_path: Caminho relativo ao projeto (ex: legal-workbench/frontend/src/App.tsx)

    Returns:
        Conteúdo do arquivo
    """
    path = PROJECT_ROOT / file_path
    if not path.exists():
        return f"✗ Arquivo não encontrado: {path}"

    try:
        content = path.read_text()
        # Limita para não estourar contexto
        if len(content) > 10000:
            content = content[:10000] + "\n... [truncado]"
        return f"Conteúdo de {file_path}:\n```\n{content}\n```"
    except Exception as e:
        return f"✗ Erro ao ler arquivo: {str(e)}"


def write_test_result(test_name: str, status: str, details: str) -> str:
    """
    Registra o resultado de um teste.

    Args:
        test_name: Nome do teste
        status: PASSOU, FALHOU, ou SKIP
        details: Detalhes do resultado

    Returns:
        Confirmação do registro
    """
    results_dir = PROJECT_ROOT / "adk-agents" / "qa_commander" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "test_name": test_name,
        "status": status,
        "details": details,
        "timestamp": timestamp
    }

    filename = f"test_{timestamp}_{test_name.replace(' ', '_')[:30]}.json"
    path = results_dir / filename

    with open(path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    icon = "✓" if status == "PASSOU" else "✗" if status == "FALHOU" else "⊘"
    return f"{icon} [{status}] {test_name}\n   Detalhes: {details}\n   Salvo em: {path}"


# --- INSTRUÇÃO DO AGENTE ---

INSTRUCTION = """# QA Commander - Agente de Testes E2E

Você é um Agente Autônomo de Quality Assurance (QA).
Sua responsabilidade é validar se o Frontend está funcionando corretamente.

## Ferramentas Disponíveis

### Navegação
- `chrome_navigate(url)`: Navega para uma URL
- `chrome_list_pages()`: Lista páginas/abas abertas
- `chrome_select_page(page_idx)`: Seleciona uma página

### Inspeção
- `chrome_snapshot()`: Captura o estado do DOM (elementos visíveis com UIDs)
- `chrome_screenshot(name)`: Salva screenshot para evidência
- `chrome_evaluate(js_code)`: Executa JavaScript na página

### Interação
- `chrome_click(uid)`: Clica em um elemento pelo UID
- `chrome_fill(uid, value)`: Preenche um input

### Validação
- `read_file(file_path)`: Lê código fonte para entender expectativas
- `write_test_result(test_name, status, details)`: Registra resultado

## Processo de Teste

1. **Entenda o Cenário**: Se necessário, leia o código fonte para saber o que esperar
2. **Navegue**: Vá para a URL do app sendo testado
3. **Inspecione**: Use snapshot para "ver" a página
4. **Interaja**: Clique, preencha campos, navegue
5. **Valide**: Compare o que vê com o esperado
6. **Documente**: Use screenshot e write_test_result para evidências

## Formato de Resultado

Sempre finalize com um resumo claro:

```
## Resultado do Teste

**Cenário**: [descrição]
**Status**: [PASSOU/FALHOU]
**Evidências**: [screenshots, snapshots relevantes]
**Observações**: [detalhes importantes]
```

## Dicas

- UIDs do snapshot são como "e15", "button-1", etc. Use-os para click/fill
- Se algo não funcionar, tente snapshot novamente (a página pode ter mudado)
- Sempre capture screenshot antes de reportar falha
- Para validar texto, use chrome_evaluate com querySelector
"""


# --- DEFINIÇÃO DO AGENTE ---

tools_list = [
    FunctionTool(func=chrome_navigate),
    FunctionTool(func=chrome_snapshot),
    FunctionTool(func=chrome_click),
    FunctionTool(func=chrome_fill),
    FunctionTool(func=chrome_screenshot),
    FunctionTool(func=chrome_list_pages),
    FunctionTool(func=chrome_select_page),
    FunctionTool(func=chrome_evaluate),
    FunctionTool(func=read_file),
    FunctionTool(func=write_test_result),
]

root_agent = Agent(
    name="qa_commander",
    model=MODEL_NAME,
    instruction=INSTRUCTION,
    description="Agente de QA que usa Chrome DevTools para testar interfaces web de forma autônoma.",
    tools=tools_list
)


# --- EXECUÇÃO DIRETA ---

if __name__ == "__main__":
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService

    # Prompt padrão
    default_prompt = """
    Teste o Trello Command Center:
    1. Navegue para http://localhost/app
    2. Verifique se a página carrega corretamente
    3. Liste os elementos visíveis (snapshot)
    4. Tire um screenshot
    5. Reporte o resultado
    """

    prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt

    print(f"🚀 QA Commander iniciando...")
    print(f"📋 Cenário: {prompt[:100]}...")
    print("-" * 60)

    try:
        # Roda o agente
        session_service = InMemorySessionService()
        runner = Runner(agent=root_agent, session_service=session_service)

        # Cria sessão
        import asyncio

        async def run():
            session = await session_service.create_session(
                agent_name="qa_commander",
                user_id="qa_user"
            )

            async for event in runner.run_async(session.id, prompt):
                if hasattr(event, 'text') and event.text:
                    print(event.text)
                if hasattr(event, 'function_call'):
                    fc = event.function_call
                    print(f"[TOOL] {fc.name}({str(dict(fc.args))[:100]}...)")

        asyncio.run(run())

    except KeyboardInterrupt:
        print("\n⏹ Interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔌 Desconectando Chrome...")
        bridge.disconnect()
        print("✓ Finalizado.")

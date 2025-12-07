"""Componente de chat."""
import streamlit as st
from typing import List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend import ContentType, ContentBlock


def render_chat_history():
    """Renderiza historico de mensagens."""
    for msg in st.session_state.get("history", []):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "blocks" in msg:
                render_assistant_message(msg)
            else:
                st.markdown(msg.get("content", ""))


def render_assistant_message(msg: Dict[str, Any]):
    """Renderiza mensagem do assistant com blocos parseados."""
    blocks: List[ContentBlock] = msg.get("blocks", [])

    if not blocks:
        st.markdown(msg.get("content", ""))
        return

    for block in blocks:
        if block.type == ContentType.TEXT:
            st.markdown(block.content)
        elif block.type == ContentType.CODE:
            st.code(block.content, language=block.language or "text")
        elif block.type == ContentType.THINKING:
            with st.status("Thinking...", expanded=False):
                st.markdown(block.content)
        elif block.type == ContentType.TOOL_CALL:
            tool_name = block.tool_name or "Tool"
            with st.expander(f"Tool: {tool_name}", expanded=False):
                st.code(block.content)
        elif block.type == ContentType.TOOL_RESULT:
            with st.expander("Result", expanded=False):
                st.code(block.content)
        elif block.type == ContentType.ERROR:
            st.error(block.content)
        elif block.type == ContentType.SYSTEM:
            st.info(block.content)


def render_chat_input():
    """Renderiza input de chat."""
    if prompt := st.chat_input("Message Claude..."):
        # Adicionar ao historico
        if "history" not in st.session_state:
            st.session_state.history = []

        st.session_state.history.append({
            "role": "user",
            "content": prompt
        })

        # Enviar para CLI se conectado
        wrapper = st.session_state.get("wrapper")
        if wrapper and wrapper.is_alive():
            wrapper.send(prompt)
        else:
            st.warning("CLI nao conectado. Inicie a conexao na sidebar.")

        st.rerun()

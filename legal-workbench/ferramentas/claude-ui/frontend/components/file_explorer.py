"""Browser de arquivos para sidebar."""
import streamlit as st
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.helpers import get_icon


def render_file_explorer(root_path: Path, max_depth: int = 2):
    """
    Renderiza file explorer recursivo.

    Args:
        root_path: Diretorio raiz
        max_depth: Profundidade maxima de recursao
    """
    if not root_path.exists():
        st.caption("Diretorio nao encontrado")
        return

    _render_directory(root_path, depth=0, max_depth=max_depth)


def _render_directory(path: Path, depth: int, max_depth: int):
    """Renderiza diretorio recursivamente."""
    if depth >= max_depth:
        return

    try:
        # Ordenar: pastas primeiro, depois arquivos, alfabeticamente
        items = sorted(
            path.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower())
        )

        # Limitar para performance
        items = items[:25]

        for item in items:
            # Ignorar arquivos/pastas ocultos
            if item.name.startswith('.'):
                continue

            # Ignorar diretorios comuns grandes
            if item.name in ('node_modules', '__pycache__', '.git', '.venv', 'venv'):
                continue

            indent = "&nbsp;" * (depth * 3)

            if item.is_dir():
                icon = get_icon('folder', "#e0e0e0", 12)
                st.markdown(
                    f"<div class='file-tree-item'>{indent}<span class='icon-svg'>{icon}</span>"
                    f"<span style='color:#e0e0e0; font-weight:bold;'>{item.name}</span></div>",
                    unsafe_allow_html=True
                )
                _render_directory(item, depth + 1, max_depth)
            else:
                icon = get_icon('file', "#666", 12)
                st.markdown(
                    f"<div class='file-tree-item'>{indent}<span class='icon-svg'>{icon}</span>"
                    f"<span style='color:#888;'>{item.name}</span></div>",
                    unsafe_allow_html=True
                )

    except PermissionError:
        pass
    except Exception:
        pass

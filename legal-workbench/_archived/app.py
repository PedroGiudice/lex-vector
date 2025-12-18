import streamlit as st
import yaml
import sys
import os
import importlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# --- CONSTANTS & CONFIG ---
DATA_PATH = Path(os.getenv("DATA_PATH_ENV", Path.home() / "juridico-data"))
CONFIG_PATH = Path("config.yaml")

st.set_page_config(
    page_title="Legal Workbench",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING (TAILWIND-LIKE DARK MODE) ---
# Injects CSS to override Streamlit defaults with a professional IDE look.
st.markdown("""
<style>
    /* Global Theme Overrides */
    .stApp { 
        background-color: #020617; /* slate-950 */
        color: #cbd5e1; /* slate-300 */
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { 
        background-color: #0f172a; /* slate-900 */
        border-right: 1px solid #1e293b; /* slate-800 */
    }
    
    /* Headers & Text */
    h1, h2, h3 { 
        color: #f8fafc !important; /* slate-50 */
        font-family: 'Source Sans Pro', sans-serif; 
        font-weight: 400;
    }
    code, .stCode, pre { 
        font-family: 'JetBrains Mono', monospace; 
        background-color: #1e293b !important;
        border: 1px solid #334155;
    }
    
    /* Metrics & Cards */
    div[data-testid="metric-container"] {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        padding: 1rem;
        border-radius: 6px;
    }
    div[data-testid="stMetricLabel"] { color: #64748b; }
    div[data-testid="stMetricValue"] { color: #e2e8f0; }

    /* Custom Buttons */
    .stButton button {
        width: 100%;
        text-align: left;
        border: 1px solid #1e293b;
        background-color: #0f172a;
        color: #94a3b8;
        transition: all 0.2s;
    }
    .stButton button:hover {
        border-color: #475569;
        background-color: #1e293b;
        color: #f1f5f9;
        transform: translateX(4px);
    }
    
    /* Hide Default Streamlit Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- CORE SYSTEM LOGIC ---

class SystemLoader:
    """Handles configuration loading and dynamic module resolution."""

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Reads the master config.yaml."""
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_module(module_id: str):
        """Dynamically imports and executes a module's render function."""
        try:
            # Dynamic import of module
            lib = importlib.import_module(f"modules.{module_id}")
            lib.render()

        except ImportError as e:
            st.error(f"FATAL: Could not load module '{module_id}'. {str(e)}")
        except AttributeError:
            st.error(f"Module '{module_id}' does not have a render() function.")
        except Exception as e:
            st.error(f"Error loading module '{module_id}': {str(e)}")

def render_dashboard():
    """Renders the main system status dashboard."""
    st.title("System Status")
    st.caption("Legal Workbench Core Services")
    st.markdown("---")
    
    # System Telemetry
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Filesystem", "Mounted", delta="~/juridico-data")
    with c2:
        st.metric("Database", "Ready", delta="DuckDB v0.9.2")
    with c3:
        st.metric("Environment", "WSL2", delta="Ubuntu 22.04")

    # Recent Activity Log
    st.markdown("#### System Log")
    log_data = [
        f"[{datetime.now().strftime('%H:%M:%S')}] INFO  Kernel initialized",
        f"[{datetime.now().strftime('%H:%M:%S')}] INFO  Config loaded from {CONFIG_PATH}",
        f"[{datetime.now().strftime('%H:%M:%S')}] WARN  Analytics module disabled by policy",
        f"[{datetime.now().strftime('%H:%M:%S')}] READY Listening for user input..."
    ]
    st.code("\n".join(log_data), language="text")

# --- MAIN EXECUTION FLOW ---

def main():
    config = SystemLoader.load_config()
    
    # Session State Init
    if "active_module" not in st.session_state:
        st.session_state.active_module = None

    # Global Sidebar
    with st.sidebar:
        st.caption("LEGAL WORKBENCH v2.4.0")
        
        st.markdown("#### SYSTEM")
        if st.button("Dashboard", key="nav_home"):
            st.session_state.active_module = None
            st.rerun()
            
        st.markdown("#### MODULES")
        for mod in config["modules"]:
            label = mod["name"]
            if not mod["active"]:
                label += " (Disabled)"
            
            if st.button(label, key=f"btn_{mod['id']}", disabled=not mod["active"]):
                st.session_state.active_module = mod["id"]
                st.rerun()

        st.markdown("#### TOOLS")
        st.markdown(
            f'''
            <a href="{os.getenv("CLAUDE_CODE_UI_URL", "http://localhost:3001")}" target="_blank" style="
                display: block;
                padding: 0.5rem 1rem;
                margin: 0.25rem 0;
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 4px;
                color: #94a3b8;
                text-decoration: none;
                font-size: 0.875rem;
                transition: all 0.2s;
            " onmouseover="this.style.backgroundColor='#1e293b'; this.style.borderColor='#475569'; this.style.color='#f1f5f9';"
               onmouseout="this.style.backgroundColor='#0f172a'; this.style.borderColor='#1e293b'; this.style.color='#94a3b8';">
                Claude Code UI
            </a>
            '''
            ,
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.code(f"PATH: {DATA_PATH}", language="text")

    # Router
    if st.session_state.active_module:
        SystemLoader.load_module(st.session_state.active_module)
    else:
        render_dashboard()

if __name__ == "__main__":
    main()

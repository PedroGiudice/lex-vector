"""
Page layouts for FastHTML Workbench.

Provides the shell layout with sidebar navigation and workspace area.
"""

from fasthtml.common import *
from typing import List, Optional
from core.loader import PluginInfo


def sidebar_item(
    plugin: PluginInfo,
    is_active: bool = False,
) -> FT:
    """
    Render a single sidebar navigation item.

    Uses HTMX to load module content into workspace.
    """
    active_cls = " active" if is_active else ""

    return Button(
        Span(plugin.icon, cls="sidebar-icon"),
        Span(plugin.name),
        cls=f"sidebar-item{active_cls}",
        hx_get=f"{plugin.mount_path}/",
        hx_target="#workspace",
        hx_swap="innerHTML transition:true",
        hx_push_url=plugin.mount_path,
        # Trigger theme switch before content loads
        hx_on__htmx_before_request=f"preloadTheme('{plugin.theme_id}')",
    )


def sidebar(
    plugins: List[PluginInfo],
    active_id: Optional[str] = None,
    app_name: str = "Legal Workbench",
) -> FT:
    """
    Render the sidebar navigation.

    Args:
        plugins: List of loaded plugins
        active_id: Currently active plugin ID
        app_name: Application name for header

    Returns:
        Sidebar nav element
    """
    return Nav(
        # Header
        Div(
            Div(app_name, cls="sidebar-title"),
            cls="sidebar-header",
        ),
        # Navigation items
        Div(
            *[
                sidebar_item(p, is_active=(p.id == active_id))
                for p in plugins
            ],
        ),
        cls="sidebar",
    )


def workspace(
    content: Optional[FT] = None,
) -> FT:
    """
    Render the main workspace area.

    This is the HTMX target for module content.
    """
    default_content = Div(
        Div("⚖️", cls="text-6xl mb-4"),
        H2("Bem-vindo ao Legal Workbench", cls="text-xl font-semibold mb-2"),
        P(
            "Selecione uma ferramenta no menu lateral para começar.",
            cls="text-secondary",
        ),
        cls="text-center py-24",
    )

    return Main(
        content if content else default_content,
        id="workspace",
        cls="app-main",
    )


def app_shell(
    plugins: List[PluginInfo],
    content: Optional[FT] = None,
    active_id: Optional[str] = None,
    app_name: str = "Legal Workbench",
) -> FT:
    """
    Render the complete application shell.

    Args:
        plugins: List of loaded plugins
        content: Initial workspace content
        active_id: Currently active plugin ID
        app_name: Application name

    Returns:
        Complete page HTML
    """
    return Div(
        sidebar(plugins, active_id, app_name),
        workspace(content),
        cls="app-layout",
    )

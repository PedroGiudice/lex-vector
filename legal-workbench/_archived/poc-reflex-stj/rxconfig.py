"""Reflex configuration for STJ PoC."""

import reflex as rx

config = rx.Config(
    app_name="poc_reflex_stj",
    api_url="http://localhost:8000",
    frontend_port=3000,
    backend_port=8000,
)

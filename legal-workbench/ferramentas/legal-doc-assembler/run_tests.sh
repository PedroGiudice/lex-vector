#!/bin/bash
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/ferramentas/legal-doc-assembler
export PYTHONPATH=.
/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/.venv/bin/pytest tests/ -v

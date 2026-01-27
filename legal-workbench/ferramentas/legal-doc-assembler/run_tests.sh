#!/bin/bash
cd /home/opc/claude-work/repos/lex-vector/legal-workbench/ferramentas/legal-doc-assembler
export PYTHONPATH=.
/home/opc/claude-work/repos/lex-vector/.venv/bin/pytest tests/ -v

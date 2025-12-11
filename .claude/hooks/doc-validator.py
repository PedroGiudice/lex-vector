#!/usr/bin/env python3
"""Validates documentation line limits."""
import os
import sys

# Support both web (CLAUDE_PROJECT_DIR) and CLI environments
BASE = os.environ.get('CLAUDE_PROJECT_DIR') or os.environ.get('PROJECT_DIR') or os.getcwd()

def validate():
    errors = []

    # Check line limits
    docs = [
        ('ARCHITECTURE.md', 100),
        ('CLAUDE.md', 100),
        ('README.md', 100),
        ('DISASTER_HISTORY.md', 80),
    ]
    for doc, limit in docs:
        path = f'{BASE}/{doc}'
        if os.path.exists(path):
            lines = sum(1 for _ in open(path))
            if lines > limit:
                errors.append(f'{doc}: {lines} linhas (limite: {limit})')

    return errors

if __name__ == '__main__':
    errors = validate()
    if errors:
        print('[doc-validator] ATENCAO:')
        for e in errors:
            print(f'  - {e}')
        sys.exit(0)  # Warning only, don't block
    print('[doc-validator] Docs OK')

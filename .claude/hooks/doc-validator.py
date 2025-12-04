#!/usr/bin/env python3
"""Validates documentation accuracy and limits."""
import os
import sys

# Support both web (CLAUDE_PROJECT_DIR) and CLI environments
BASE = os.environ.get('CLAUDE_PROJECT_DIR') or os.environ.get('PROJECT_DIR') or os.getcwd()

def count_dirs(path):
    """Count subdirectories."""
    if not os.path.exists(path):
        return 0
    return len([d for d in os.listdir(path) if os.path.isdir(f'{path}/{d}')])

def count_files(path, ext='.md'):
    """Count files with extension."""
    if not os.path.exists(path):
        return 0
    return len([f for f in os.listdir(path) if f.endswith(ext) and f != 'README.md'])

def validate():
    errors = []

    # Actual counts
    agents_python = count_dirs(f'{BASE}/agentes')
    agents_claude = count_files(f'{BASE}/.claude/agents')
    skills_custom = count_dirs(f'{BASE}/skills')

    # Check README numbers
    readme = f'{BASE}/README.md'
    if os.path.exists(readme):
        content = open(readme).read()
        checks = [
            (f'| Agentes Python | {agents_python} |', f'Agentes Python: {agents_python}'),
            (f'| Agentes Claude | {agents_claude} |', f'Agentes Claude: {agents_claude}'),
            (f'| Skills custom | {skills_custom} |', f'Skills custom: {skills_custom}'),
        ]
        for expected, name in checks:
            if expected not in content:
                errors.append(f'README desatualizado: {name}')

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

# Instalacao no Claude Desktop

## Download

Arquivo ZIP pronto: `prompt-library-skill.zip`

## Instalacao

1. Abra **Claude Desktop**
2. Va em **Settings** → **Capabilities**
3. Clique em **Upload Skill**
4. Selecione o arquivo `prompt-library-skill.zip`

## Uso

Apos upload, a skill estara disponivel automaticamente.

Ative digitando:
```
skill: prompt-library
```

Ou mencione palavras-chave:
- "buscar prompt"
- "template de prompt"
- "renderizar prompt"

## Conteudo do ZIP

```
prompt-library-skill.zip
├── SKILL.md        # Instrucoes para Claude
├── README.md       # Documentacao
└── core/           # Biblioteca Python
    ├── __init__.py
    ├── models.py   # Schemas Pydantic
    ├── loader.py   # Carregador YAML
    ├── renderer.py # Renderizacao
    └── search.py   # Busca
```

## Regenerar ZIP

Se fizer alteracoes, regenere com:

```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/ferramentas/prompt-library
zip -r prompt-library-skill.zip SKILL.md README.md core/ -x "*.pyc" -x "__pycache__/*"
```

## Requisitos

- Claude Desktop (Pro, Max, Team ou Enterprise)
- Feature preview "Skills" habilitada

---

**Fonte:** [Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)

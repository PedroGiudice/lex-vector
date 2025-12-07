"""
Schemas Pydantic para templates de prompt.

Este módulo define as estruturas de dados para:
- PromptVariable: variáveis preenchíveis em templates
- PromptTemplate: template completo com metadados
- PromptLibrary: coleção de prompts carregados
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class PromptVariable(BaseModel):
    """Define uma variável preenchível no template."""

    nome: str = Field(..., description="Nome da variável no template (usado em {nome})")
    label: str = Field(..., description="Label exibido na UI")
    tipo: Literal["text", "textarea", "select"] = "text"
    obrigatorio: bool = True
    opcoes: Optional[List[str]] = None  # Para tipo "select"
    placeholder: Optional[str] = None
    default: Optional[str] = None


class PromptTemplate(BaseModel):
    """Template de prompt completo."""

    id: str = Field(..., description="Identificador único, ex: 'hook_error'")
    titulo: str = Field(..., description="Nome legível, ex: 'User Prompt Submit Hook Error'")
    categoria: str = Field(..., description="Categoria principal, ex: 'troubleshooting'")
    tags: List[str] = Field(default_factory=list, description="Tags para busca")
    descricao: str = Field(..., description="Descrição curta do propósito")
    variaveis: List[PromptVariable] = Field(default_factory=list)
    template: str = Field(..., description="Texto do prompt com placeholders {variavel}")

    # Metadados opcionais
    autor: Optional[str] = None
    versao: str = "1.0"
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None


class PromptLibrary(BaseModel):
    """Coleção de prompts carregados."""

    prompts: List[PromptTemplate] = Field(default_factory=list)

    def get_by_id(self, id: str) -> Optional[PromptTemplate]:
        """Busca prompt por ID."""
        return next((p for p in self.prompts if p.id == id), None)

    def get_by_categoria(self, categoria: str) -> List[PromptTemplate]:
        """Lista prompts de uma categoria."""
        return [p for p in self.prompts if p.categoria == categoria]

    def list_categorias(self) -> List[str]:
        """Lista categorias únicas."""
        return sorted(set(p.categoria for p in self.prompts))

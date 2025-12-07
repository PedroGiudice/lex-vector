"""
Carregador de templates de prompt a partir de arquivos YAML.

Responsabilidades:
- Carregar arquivos .yaml recursivamente
- Validar contra schema PromptTemplate
- Logar erros sem quebrar (skip inválidos)
"""

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from .models import PromptLibrary, PromptTemplate

logger = logging.getLogger(__name__)


def load_prompt(file_path: Path) -> Optional[PromptTemplate]:
    """
    Carrega e valida um único arquivo YAML.

    Args:
        file_path: Caminho para o arquivo YAML

    Returns:
        PromptTemplate validado ou None se inválido
    """
    try:
        # 1. Tentar abrir e ler arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 2. Verificar se arquivo está vazio
        if data is None:
            logger.warning(f"Arquivo vazio: {file_path}")
            return None

        # 3. Validar com Pydantic v2
        template = PromptTemplate.model_validate(data)
        logger.debug(f"Template carregado com sucesso: {template.id} ({file_path})")
        return template

    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {file_path}")
        return None

    except yaml.YAMLError as e:
        logger.error(f"Erro ao parsear YAML em {file_path}: {e}")
        return None

    except ValidationError as e:
        logger.error(f"Erro de validação em {file_path}: {e}")
        return None

    except Exception as e:
        logger.error(f"Erro inesperado ao carregar {file_path}: {e}")
        return None


def load_library(prompts_dir: Path) -> PromptLibrary:
    """
    Carrega todos os prompts de um diretório.

    Args:
        prompts_dir: Diretório raiz dos prompts

    Returns:
        PromptLibrary com todos os prompts válidos
    """
    prompts = []

    # 1. Verificar se diretório existe
    if not prompts_dir.exists():
        logger.warning(f"Diretório de prompts não existe: {prompts_dir}")
        return PromptLibrary(prompts=[])

    if not prompts_dir.is_dir():
        logger.warning(f"Caminho não é um diretório: {prompts_dir}")
        return PromptLibrary(prompts=[])

    # 2. Buscar todos os arquivos YAML recursivamente
    yaml_files = list(prompts_dir.glob("**/*.yaml")) + list(prompts_dir.glob("**/*.yml"))

    if not yaml_files:
        logger.info(f"Nenhum arquivo YAML encontrado em {prompts_dir}")
        return PromptLibrary(prompts=[])

    # 3. Carregar cada arquivo
    logger.info(f"Carregando prompts de {prompts_dir}...")
    for file_path in yaml_files:
        template = load_prompt(file_path)
        if template is not None:
            prompts.append(template)

    # 4. Logar resultado
    logger.info(f"✓ {len(prompts)} prompts carregados de {len(yaml_files)} arquivos encontrados")

    # 5. Retornar biblioteca
    return PromptLibrary(prompts=prompts)


def reload_library(prompts_dir: Path, library: PromptLibrary) -> PromptLibrary:
    """
    Recarrega biblioteca (para hot-reload na UI).

    Args:
        prompts_dir: Diretório raiz dos prompts
        library: Biblioteca atual (ignorada, recarrega do zero)

    Returns:
        Nova PromptLibrary com prompts atualizados
    """
    logger.info("Recarregando biblioteca de prompts...")
    return load_library(prompts_dir)

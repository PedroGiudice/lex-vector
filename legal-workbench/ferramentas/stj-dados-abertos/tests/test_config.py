"""Tests for config.py CKAN configuration."""
import pytest
from config import (
    CKAN_BASE_URL,
    CKAN_DATASETS,
    get_ckan_package_url,
    get_orgao_dataset_id,
)


def test_ckan_base_url_correct():
    """CKAN base URL should point to dadosabertos.web.stj.jus.br."""
    assert CKAN_BASE_URL == "https://dadosabertos.web.stj.jus.br"


def test_ckan_datasets_has_all_orgaos():
    """Should have mapping for all 10 orgaos + integras."""
    expected_orgaos = [
        "corte_especial",
        "primeira_secao", "segunda_secao", "terceira_secao",
        "primeira_turma", "segunda_turma", "terceira_turma",
        "quarta_turma", "quinta_turma", "sexta_turma",
    ]
    for orgao in expected_orgaos:
        assert orgao in CKAN_DATASETS


def test_get_ckan_package_url():
    """Should return correct CKAN API URL."""
    url = get_ckan_package_url("primeira_turma")
    assert url == "https://dadosabertos.web.stj.jus.br/api/3/action/package_show?id=espelhos-de-acordaos-primeira-turma"


def test_get_orgao_dataset_id():
    """Should map orgao key to dataset ID."""
    assert get_orgao_dataset_id("corte_especial") == "espelhos-de-acordaos-corte-especial"
    assert get_orgao_dataset_id("primeira_turma") == "espelhos-de-acordaos-primeira-turma"


def test_get_orgao_dataset_id_invalid():
    """Invalid orgao should raise KeyError."""
    with pytest.raises(KeyError):
        get_orgao_dataset_id("invalid_orgao")


def test_integras_dataset_id_exists():
    from config import INTEGRAS_DATASET_ID
    assert INTEGRAS_DATASET_ID == "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"

def test_integras_dirs_exist():
    from config import INTEGRAS_DIR, INTEGRAS_STAGING_DIR, INTEGRAS_TEXTOS_DIR
    assert INTEGRAS_DIR is not None
    assert INTEGRAS_STAGING_DIR is not None
    assert INTEGRAS_TEXTOS_DIR is not None

def test_get_integras_dataset_id():
    from config import get_integras_dataset_id
    assert get_integras_dataset_id() == "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"

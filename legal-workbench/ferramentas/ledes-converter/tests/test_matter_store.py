import sqlite3
import tempfile
import os

import pytest

from api.matter_store import MatterStore, Matter


@pytest.fixture
def db_path():
    """Cria um arquivo temporario para cada teste."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def store(db_path):
    """MatterStore com banco temporario isolado."""
    return MatterStore(db_path=db_path)


def test_seed_initial_data(store):
    """Verifica que os 3 matters sao criados automaticamente no seed."""
    matters = store.list_all()
    assert len(matters) == 3

    names = {m.matter_name for m in matters}
    assert "CMR General Litigation Matters" in names
    assert "BRA/STLandATDIL/CRM/Governance" in names
    assert "FY26 - General Employment Advice (Brazil)" in names

    # Verifica campos do primeiro seed
    cmr = store.get("CMR General Litigation Matters")
    assert cmr is not None
    assert cmr.matter_id == "LS-2020-05805"
    assert cmr.client_id == "Salesforce, Inc."
    assert cmr.law_firm_id == "SF004554"
    assert cmr.timekeeper_id == "CMR"
    assert cmr.unit_cost == 300.00
    assert cmr.created_at != ""
    assert cmr.updated_at != ""


def test_list_all(store):
    """Lista retorna 3 matters do seed, ordenados por nome."""
    matters = store.list_all()
    assert len(matters) == 3
    # Verificar ordenacao alfabetica
    names = [m.matter_name for m in matters]
    assert names == sorted(names)


def test_get_existing(store):
    """Busca por nome funciona para matter existente."""
    matter = store.get("BRA/STLandATDIL/CRM/Governance")
    assert matter is not None
    assert matter.matter_id == "LS-2025-23274"
    assert matter.law_firm_name == "C. M. Rodrigues Sociedade de Advogados"


def test_get_nonexistent(store):
    """Retorna None para matter inexistente."""
    result = store.get("Matter Que Nao Existe")
    assert result is None


def test_create(store):
    """Cria novo matter e verifica que get retorna."""
    new_matter = Matter(
        matter_name="Novo Caso Teste",
        matter_id="LS-2026-99999",
        client_matter_id="CLT-001",
        client_id="Acme Corp",
        client_name="Acme Corp",
        law_firm_id="ACME001",
        law_firm_name="Acme Law Firm",
        timekeeper_id="JD",
        timekeeper_name="DOE, JOHN",
        timekeeper_classification="ASSOCIATE",
        unit_cost=250.00,
    )
    created = store.create(new_matter)
    assert created.matter_name == "Novo Caso Teste"
    assert created.created_at != ""
    assert created.updated_at != ""

    # Verificar persistencia
    fetched = store.get("Novo Caso Teste")
    assert fetched is not None
    assert fetched.matter_id == "LS-2026-99999"
    assert fetched.unit_cost == 250.00

    # Verificar que agora temos 4
    assert len(store.list_all()) == 4


def test_create_duplicate(store):
    """Tenta criar com mesmo nome, deve levantar IntegrityError."""
    duplicate = Matter(
        matter_name="CMR General Litigation Matters",
        matter_id="LS-DUPLICADO",
        client_matter_id="",
        client_id="Outro Client",
        client_name="Outro",
        law_firm_id="OUTRO001",
        law_firm_name="Outra Firma",
        timekeeper_id="XX",
        timekeeper_name="TESTE",
        timekeeper_classification="PARTNR",
        unit_cost=100.00,
    )
    with pytest.raises(sqlite3.IntegrityError):
        store.create(duplicate)


def test_update(store):
    """Atualiza campos e verifica que updated_at muda."""
    original = store.get("CMR General Litigation Matters")
    assert original is not None
    original_updated_at = original.updated_at

    updated = store.update("CMR General Litigation Matters", {
        "unit_cost": 350.00,
        "timekeeper_classification": "SENIOR_PARTNR",
    })

    assert updated is not None
    assert updated.unit_cost == 350.00
    assert updated.timekeeper_classification == "SENIOR_PARTNR"
    assert updated.updated_at != original_updated_at
    # Campos nao alterados permanecem iguais
    assert updated.matter_id == "LS-2020-05805"
    assert updated.client_id == "Salesforce, Inc."


def test_update_nonexistent(store):
    """Retorna None ao tentar atualizar matter inexistente."""
    result = store.update("Matter Fantasma", {"unit_cost": 999.00})
    assert result is None


def test_delete(store):
    """Remove matter e verifica que get retorna None."""
    assert store.get("CMR General Litigation Matters") is not None

    deleted = store.delete("CMR General Litigation Matters")
    assert deleted is True

    assert store.get("CMR General Litigation Matters") is None
    assert len(store.list_all()) == 2


def test_delete_nonexistent(store):
    """Retorna False ao tentar deletar matter inexistente."""
    result = store.delete("Matter Que Nao Existe")
    assert result is False

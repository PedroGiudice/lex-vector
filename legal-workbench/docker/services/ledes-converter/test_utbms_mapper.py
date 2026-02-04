"""
Test suite for UTBMS Code Mapper.

Tests task code and activity code inference from line item descriptions.
"""
import pytest
from api.utbms_mapper import infer_task_code, infer_activity_code


class TestTaskCodeMapping:
    """Test UTBMS task code inference from line item descriptions."""

    def test_appeals_task_code(self):
        """Appeals-related descriptions should map to L510."""
        assert infer_task_code("Draft and file Special Appeal") == "L510"
        assert infer_task_code("Prepare recurso especial") == "L510"
        assert infer_task_code("File agravo de instrumento") == "L510"
        assert infer_task_code("STJ appeal preparation") == "L510"

    def test_pleadings_task_code(self):
        """Pleadings descriptions should map to L210."""
        assert infer_task_code("Prepare defense motion") == "L210"
        assert infer_task_code("Draft contestação") == "L210"
        assert infer_task_code("File answer to complaint") == "L210"

    def test_motions_task_code(self):
        """Motion descriptions should map to L250."""
        assert infer_task_code("File motion to dismiss") == "L250"
        assert infer_task_code("Prepare petition for relief") == "L250"
        assert infer_task_code("Draft requerimento") == "L250"

    def test_settlement_task_code(self):
        """Settlement/ADR descriptions should map to L160."""
        assert infer_task_code("Settlement negotiation") == "L160"
        assert infer_task_code("Mediation preparation") == "L160"
        assert infer_task_code("Draft acordo") == "L160"

    def test_research_task_code(self):
        """Research descriptions should map to L110."""
        assert infer_task_code("Legal research on precedents") == "L110"
        assert infer_task_code("Pesquisa jurisprudencial") == "L110"
        assert infer_task_code("Case law research") == "L110"

    def test_default_task_code(self):
        """Unknown descriptions should return default L100."""
        assert infer_task_code("General legal work") == "L100"
        assert infer_task_code("") == "L100"
        assert infer_task_code("xyz random text") == "L100"

    def test_custom_default(self):
        """Should accept custom default code."""
        assert infer_task_code("unknown work", default="L999") == "L999"


class TestActivityCodeMapping:
    """Test UTBMS activity code inference from line item descriptions."""

    def test_draft_activity_code(self):
        """Draft/write descriptions should map to A103."""
        assert infer_activity_code("Draft motion") == "A103"
        assert infer_activity_code("Prepare document") == "A103"
        assert infer_activity_code("Write brief") == "A103"
        assert infer_activity_code("Redigir peticao") == "A103"

    def test_review_activity_code(self):
        """Review/analyze descriptions should map to A104."""
        assert infer_activity_code("Review contract") == "A104"
        assert infer_activity_code("Analyze documents") == "A104"
        assert infer_activity_code("Revisar processo") == "A104"

    def test_communicate_activity_code(self):
        """Communication descriptions should map to A106."""
        assert infer_activity_code("Client meeting") == "A106"
        assert infer_activity_code("Phone conference") == "A106"
        assert infer_activity_code("Email correspondence") == "A106"
        assert infer_activity_code("Reuniao com cliente") == "A106"

    def test_research_activity_code(self):
        """Research descriptions should map to A102."""
        assert infer_activity_code("Legal research") == "A102"
        assert infer_activity_code("Research case law") == "A102"
        assert infer_activity_code("Pesquisa jurisprudencial") == "A102"

    def test_appear_activity_code(self):
        """Appearance descriptions should map to A105."""
        assert infer_activity_code("Court appearance") == "A105"
        assert infer_activity_code("Attend hearing") == "A105"
        assert infer_activity_code("Audiencia") == "A105"

    def test_default_activity_code(self):
        """Unknown descriptions should return default A103."""
        assert infer_activity_code("General work") == "A103"
        assert infer_activity_code("") == "A103"

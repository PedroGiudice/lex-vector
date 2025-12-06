"""
Document Engine - Core rendering logic for legal document generation.

Uses docxtpl with Jinja2 and custom normalization filters.
Fault-tolerant: undefined variables remain visible in output.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2
from jinja2 import DebugUndefined
from docxtpl import DocxTemplate
from rich.console import Console
from rich.table import Table

from .normalizers import (
    normalize_name,
    normalize_address,
    format_cpf,
    format_cnpj,
    format_cep,
    format_oab,
    normalize_whitespace,
    normalize_punctuation,
    normalize_all,
)

console = Console()


class DocumentEngine:
    """
    Document rendering engine for legal documents.

    Features:
        - Jinja2 templating with docxtpl
        - Fault-tolerant: undefined variables show {{ var_name }} in output
        - Custom filters for Brazilian document formatting
        - Automatic text normalization

    Usage:
        engine = DocumentEngine()
        engine.render(
            template_path="template.docx",
            data={"nome": "João da Silva", "cpf": "12345678901"},
            output_path="output.docx"
        )
    """

    def __init__(self, auto_normalize: bool = True):
        """
        Initialize the document engine.

        Args:
            auto_normalize: If True, automatically apply text normalization
                to string values in data dict.
        """
        self.auto_normalize = auto_normalize
        self._setup_jinja_env()

    def _setup_jinja_env(self) -> jinja2.Environment:
        """
        Configure Jinja2 environment with:
            - DebugUndefined: keeps {{ var }} visible if undefined
            - Custom filters for Brazilian formatting
        """
        self.jinja_env = jinja2.Environment(
            undefined=DebugUndefined,
            autoescape=False,  # Don't escape for docx
        )

        # Register custom filters
        self.jinja_env.filters['nome'] = normalize_name
        self.jinja_env.filters['endereco'] = normalize_address
        self.jinja_env.filters['cpf'] = format_cpf
        self.jinja_env.filters['cnpj'] = format_cnpj
        self.jinja_env.filters['cep'] = format_cep
        self.jinja_env.filters['oab'] = format_oab
        self.jinja_env.filters['texto'] = lambda x: normalize_punctuation(
            normalize_whitespace(x)
        )

        return self.jinja_env

    def _preprocess_data(
        self,
        data: Dict[str, Any],
        field_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Preprocess data before rendering.

        If auto_normalize is True and field_types not provided,
        applies basic whitespace normalization to all string values.

        If field_types is provided, uses normalize_all() for type-specific
        normalization.

        Args:
            data: Raw data dictionary
            field_types: Optional dict mapping field names to types
                ('name', 'address', 'cpf', 'cnpj', 'cep', 'oab', 'text', 'raw')

        Returns:
            Preprocessed data dictionary
        """
        if not self.auto_normalize:
            return data

        if field_types:
            return normalize_all(data, field_types)

        # Default: apply whitespace normalization to all strings
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = normalize_whitespace(value)
            elif isinstance(value, dict):
                result[key] = self._preprocess_data(value)
            elif isinstance(value, list):
                result[key] = [
                    self._preprocess_data(item) if isinstance(item, dict)
                    else normalize_whitespace(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def render(
        self,
        template_path: str | Path,
        data: Dict[str, Any],
        output_path: str | Path,
        field_types: Optional[Dict[str, str]] = None,
    ) -> Path:
        """
        Render a document from template and data.

        Args:
            template_path: Path to .docx template file
            data: Dictionary with template variables
            output_path: Path for output .docx file
            field_types: Optional dict mapping field names to normalization types

        Returns:
            Path to the generated document

        Raises:
            FileNotFoundError: If template doesn't exist
            ValueError: If template is invalid
        """
        template_path = Path(template_path)
        output_path = Path(output_path)

        # Validate template exists
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Preprocess data
        processed_data = self._preprocess_data(data, field_types)

        # Load template with custom Jinja environment
        try:
            doc = DocxTemplate(template_path)
            doc.render(processed_data, self.jinja_env)
        except Exception as e:
            raise ValueError(f"Error rendering template: {e}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save document
        doc.save(output_path)

        console.print(f"[green]✔[/green] Document saved: {output_path}")

        return output_path

    def render_from_json(
        self,
        template_path: str | Path,
        json_path: str | Path,
        output_path: str | Path,
        field_types: Optional[Dict[str, str]] = None,
    ) -> Path:
        """
        Render document from template and JSON data file.

        Args:
            template_path: Path to .docx template
            json_path: Path to JSON file with data
            output_path: Path for output document
            field_types: Optional normalization type mapping

        Returns:
            Path to generated document
        """
        json_path = Path(json_path)

        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.render(template_path, data, output_path, field_types)

    def get_template_variables(self, template_path: str | Path) -> List[str]:
        """
        Extract variable names from a template.

        Useful for understanding what data a template expects.

        Args:
            template_path: Path to .docx template

        Returns:
            List of variable names found in template
        """
        template_path = Path(template_path)

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        doc = DocxTemplate(template_path)
        # Use our Jinja2 environment which has custom filters registered
        variables = doc.get_undeclared_template_variables(self.jinja_env)

        return sorted(list(variables))

    def validate_data(
        self,
        template_path: str | Path,
        data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Validate data against template requirements.

        Args:
            template_path: Path to .docx template
            data: Data dictionary to validate

        Returns:
            Dict with 'missing' and 'extra' keys listing field names
        """
        required = set(self.get_template_variables(template_path))
        provided = set(data.keys())

        return {
            'missing': sorted(list(required - provided)),
            'extra': sorted(list(provided - required)),
        }

    def print_validation_report(
        self,
        template_path: str | Path,
        data: Dict[str, Any]
    ) -> None:
        """Print a formatted validation report to console."""
        validation = self.validate_data(template_path, data)

        table = Table(title="Data Validation Report")
        table.add_column("Status", style="bold")
        table.add_column("Fields")

        if validation['missing']:
            table.add_row(
                "[yellow]Missing[/yellow]",
                ", ".join(validation['missing'])
            )
        else:
            table.add_row("[green]Missing[/green]", "None")

        if validation['extra']:
            table.add_row(
                "[blue]Extra[/blue]",
                ", ".join(validation['extra'])
            )
        else:
            table.add_row("[green]Extra[/green]", "None")

        console.print(table)

        if validation['missing']:
            console.print(
                "\n[yellow]⚠ Warning:[/yellow] Missing fields will appear "
                "as {{ field_name }} in output."
            )

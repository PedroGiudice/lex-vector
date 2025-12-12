"""
Template Builder for creating Jinja2 DOCX templates.

Workflow:
1. Load source DOCX
2. Preview content
3. Detect patterns automatically OR select text manually
4. Replace text with Jinja2 variables
5. Save template + metadata
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from docx import Document

from .docx_parser import DocxParser
from .pattern_detector import PatternDetector


@dataclass
class FieldReplacement:
    """Represents a text-to-field replacement."""
    original_text: str
    field_name: str
    filter_name: str
    jinja_template: str = ""

    def __post_init__(self):
        if self.filter_name:
            self.jinja_template = f"{{{{ {self.field_name} | {self.filter_name} }}}}"
        else:
            self.jinja_template = f"{{{{ {self.field_name} }}}}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.field_name,
            'filter': self.filter_name,
            'original_sample': self.original_text[:50],
            'jinja': self.jinja_template
        }


class TemplateBuilder:
    """
    Builder for creating Jinja2 DOCX templates from plain documents.

    Features:
    - Load and preview DOCX content
    - Automatic pattern detection (CPF, CNPJ, etc.)
    - Manual text selection for field creation
    - Save template with metadata
    """

    def __init__(self, source_path: str | Path):
        """
        Initialize builder with source DOCX.

        Args:
            source_path: Path to source DOCX file
        """
        self.source_path = Path(source_path)
        self.parser = DocxParser(source_path)
        self.detector = PatternDetector()
        self.document = Document(str(source_path))

        # Track replacements
        self.replacements: List[FieldReplacement] = []

        # Cache original text
        self._original_text = self.parser.get_full_text()
        self._modified_text = self._original_text

    def get_full_text(self) -> str:
        """Get full document text for preview."""
        return self._original_text

    def get_modified_text(self) -> str:
        """Get text with current replacements applied."""
        return self._modified_text

    def get_paragraphs(self) -> List[Dict[str, Any]]:
        """Get structured paragraphs for UI display."""
        return self.parser.extract_paragraphs()

    def get_structure(self) -> Dict[str, int]:
        """Get document structure summary."""
        return self.parser.get_structure_summary()

    def detect_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect all patterns in document.

        Returns:
            List of detected patterns with positions and suggested fields
        """
        return self.detector.detect_all(self._original_text)

    def add_field_replacement(
        self,
        text: str,
        field_name: str,
        filter_name: str = ""
    ) -> bool:
        """
        Add a text-to-field replacement.

        Args:
            text: Original text to replace
            field_name: Jinja2 field name
            filter_name: Optional filter (e.g., 'cpf', 'nome')

        Returns:
            True if replacement was added successfully
        """
        if text not in self._modified_text:
            return False

        replacement = FieldReplacement(
            original_text=text,
            field_name=field_name,
            filter_name=filter_name
        )

        # Apply replacement to modified text
        self._modified_text = self._modified_text.replace(
            text,
            replacement.jinja_template
        )

        self.replacements.append(replacement)
        return True

    def apply_detected_pattern(self, match: Dict[str, Any]) -> bool:
        """
        Apply a detected pattern as a field replacement.

        Args:
            match: Pattern match dict from detect_patterns()

        Returns:
            True if applied successfully
        """
        return self.add_field_replacement(
            text=match['value'],
            field_name=match['suggested_field'],
            filter_name=match['filter']
        )

    def remove_replacement(self, field_name: str) -> bool:
        """
        Remove a replacement by field name.

        Args:
            field_name: Name of field to remove

        Returns:
            True if removed successfully
        """
        for i, r in enumerate(self.replacements):
            if r.field_name == field_name:
                # Restore original text
                self._modified_text = self._modified_text.replace(
                    r.jinja_template,
                    r.original_text
                )
                self.replacements.pop(i)
                return True
        return False

    def reset(self) -> None:
        """Reset all replacements."""
        self.replacements = []
        self._modified_text = self._original_text

    def get_fields(self) -> List[Dict[str, Any]]:
        """Get list of current fields."""
        return [r.to_dict() for r in self.replacements]

    def save_template(
        self,
        output_dir: str | Path,
        template_name: str,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Save template DOCX and metadata JSON.

        Args:
            output_dir: Directory to save template
            template_name: Name for template (used as filename)
            description: Template description
            tags: Optional tags for categorization

        Returns:
            Dict with success status and file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize template name
        safe_name = re.sub(r'[^\w\-]', '_', template_name.lower())

        docx_path = output_dir / f"{safe_name}.docx"
        meta_path = output_dir / f"{safe_name}.json"

        try:
            # Apply replacements to document
            self._apply_replacements_to_document()

            # Save DOCX
            self.document.save(str(docx_path))

            # Create metadata
            metadata = {
                'name': template_name,
                'safe_name': safe_name,
                'description': description,
                'tags': tags or [],
                'fields': self.get_fields(),
                'created_at': datetime.now().isoformat(),
                'source_file': self.source_path.name,
                'structure': self.get_structure()
            }

            # Save metadata
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            return {
                'success': True,
                'docx_path': str(docx_path),
                'meta_path': str(meta_path),
                'fields_count': len(self.replacements)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _apply_replacements_to_document(self) -> None:
        """Apply all replacements to the actual DOCX document."""
        for para in self.document.paragraphs:
            for replacement in self.replacements:
                if replacement.original_text in para.text:
                    # Replace in each run
                    for run in para.runs:
                        if replacement.original_text in run.text:
                            run.text = run.text.replace(
                                replacement.original_text,
                                replacement.jinja_template
                            )
                    # Handle text split across runs
                    if replacement.original_text in para.text:
                        full_text = para.text.replace(
                            replacement.original_text,
                            replacement.jinja_template
                        )
                        # Clear existing runs and add new
                        for run in para.runs:
                            run.text = ""
                        if para.runs:
                            para.runs[0].text = full_text

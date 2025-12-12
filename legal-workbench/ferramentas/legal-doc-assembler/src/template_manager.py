"""
Template Manager for listing, searching, and managing saved templates.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class TemplateManager:
    """
    Manages saved templates in a directory.

    Templates consist of:
    - {name}.docx: The template file with Jinja2 variables
    - {name}.json: Metadata (fields, description, tags, etc.)
    """

    def __init__(self, templates_dir: str | Path):
        """
        Initialize manager with templates directory.

        Args:
            templates_dir: Directory containing templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates.

        Returns:
            List of template metadata dicts, sorted by creation date (newest first)
        """
        templates = []

        for meta_path in self.templates_dir.glob('*.json'):
            try:
                with open(meta_path, encoding='utf-8') as f:
                    meta = json.load(f)

                # Check if DOCX exists
                docx_path = meta_path.with_suffix('.docx')
                if docx_path.exists():
                    meta['docx_path'] = str(docx_path)
                    meta['meta_path'] = str(meta_path)
                    templates.append(meta)

            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by creation date (newest first)
        templates.sort(
            key=lambda t: t.get('created_at', ''),
            reverse=True
        )

        return templates

    def get_template(self, safe_name: str) -> Optional[Dict[str, Any]]:
        """
        Get template details by safe name.

        Args:
            safe_name: Template's safe name (filename without extension)

        Returns:
            Template metadata dict or None if not found
        """
        meta_path = self.templates_dir / f"{safe_name}.json"
        docx_path = self.templates_dir / f"{safe_name}.docx"

        if not meta_path.exists() or not docx_path.exists():
            return None

        try:
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            meta['docx_path'] = str(docx_path)
            meta['meta_path'] = str(meta_path)
            return meta
        except (json.JSONDecodeError, KeyError):
            return None

    def search(
        self,
        query: str,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query (case-insensitive)
            tags: Optional list of tags to filter by

        Returns:
            List of matching template metadata dicts
        """
        query_lower = query.lower()
        results = []

        for template in self.list_templates():
            # Search in name and description
            name_match = query_lower in template.get('name', '').lower()
            desc_match = query_lower in template.get('description', '').lower()
            tag_match = any(
                query_lower in tag.lower()
                for tag in template.get('tags', [])
            )

            if name_match or desc_match or tag_match:
                # Additional tag filter if specified
                if tags:
                    template_tags = set(template.get('tags', []))
                    if not set(tags).intersection(template_tags):
                        continue
                results.append(template)

        return results

    def delete_template(self, safe_name: str) -> bool:
        """
        Delete a template and its metadata.

        Args:
            safe_name: Template's safe name

        Returns:
            True if deleted successfully
        """
        meta_path = self.templates_dir / f"{safe_name}.json"
        docx_path = self.templates_dir / f"{safe_name}.docx"

        deleted = False

        if meta_path.exists():
            meta_path.unlink()
            deleted = True

        if docx_path.exists():
            docx_path.unlink()
            deleted = True

        return deleted

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all templates.

        Returns:
            Sorted list of unique tags
        """
        tags = set()
        for template in self.list_templates():
            tags.update(template.get('tags', []))
        return sorted(tags)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about saved templates.

        Returns:
            Dict with counts and stats
        """
        templates = self.list_templates()

        total_fields = sum(
            len(t.get('fields', []))
            for t in templates
        )

        return {
            'total_templates': len(templates),
            'total_fields': total_fields,
            'tags': self.get_all_tags(),
            'most_recent': templates[0]['name'] if templates else None
        }

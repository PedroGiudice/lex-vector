"""
Utility functions for batch document processing.

Provides helpers for filename sanitization, performance estimation,
and pre-flight validation of batch input data.
"""

import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import json


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Sanitize a string for use as a safe filename.

    Removes or replaces characters that are illegal in filenames:
        - Removes: / \\ : * ? " < > |
        - Replaces spaces with underscores
        - Collapses multiple underscores
        - Truncates to max_length

    Args:
        name: Original filename (without extension)
        max_length: Maximum filename length (default 100)

    Returns:
        Sanitized filename safe for all OS

    Examples:
        >>> sanitize_filename("João da Silva")
        'Joao_da_Silva'
        >>> sanitize_filename("Processo 123/2024")
        'Processo_123_2024'
        >>> sanitize_filename("Doc: Teste <versão 1>")
        'Doc_Teste_versao_1'
    """
    if not name:
        return "unnamed"

    # Remove diacritics (accents) - convert João → Joao
    import unicodedata
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')

    # Replace illegal characters with underscore
    name = re.sub(r'[/\\:*?"<>|]', '_', name)

    # Replace spaces with underscores
    name = name.replace(' ', '_')

    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

    # Truncate to max length
    if len(name) > max_length:
        name = name[:max_length].rstrip('_')

    # Ensure not empty after sanitization
    return name if name else "unnamed"


def estimate_batch_time(
    num_docs: int,
    workers: int = 8,
    avg_time_per_doc: float = 0.2
) -> float:
    """
    Estimate processing time for a batch of documents.

    Simple parallel processing model:
        time = (num_docs / workers) * avg_time_per_doc

    Args:
        num_docs: Number of documents to process
        workers: Number of parallel workers
        avg_time_per_doc: Average time per document in seconds (default 0.2s)

    Returns:
        Estimated time in seconds

    Examples:
        >>> estimate_batch_time(100, workers=8)
        2.5
        >>> estimate_batch_time(500, workers=4)
        25.0
    """
    if num_docs <= 0:
        return 0.0

    workers = max(1, workers)  # Ensure at least 1 worker
    return (num_docs / workers) * avg_time_per_doc


def validate_batch_input(
    json_dir: Path,
    template_path: Path,
    required_extensions: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Perform pre-flight validation of batch input parameters.

    Validates:
        - json_dir exists and is a directory
        - template_path exists and is a file
        - template has correct extension (.docx)
        - json_dir contains JSON files
        - JSON files are readable and parseable

    Args:
        json_dir: Directory containing JSON files
        template_path: Path to template file
        required_extensions: List of allowed template extensions (default: ['.docx'])

    Returns:
        Dictionary with validation results:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'json_files': List[Path],
                'template_hash': str
            }

    Examples:
        >>> validate_batch_input(Path('json_inputs/'), Path('template.docx'))
        {
            'valid': True,
            'errors': [],
            'warnings': [],
            'json_files': [Path('json_inputs/card_1.json'), ...],
            'template_hash': 'sha256:abc123...'
        }
    """
    if required_extensions is None:
        required_extensions = ['.docx']

    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'json_files': [],
        'template_hash': None
    }

    # Validate json_dir
    if not json_dir.exists():
        result['errors'].append(f"JSON directory does not exist: {json_dir}")
        result['valid'] = False
    elif not json_dir.is_dir():
        result['errors'].append(f"JSON path is not a directory: {json_dir}")
        result['valid'] = False
    else:
        # Find JSON files
        json_files = sorted(json_dir.glob('*.json'))
        if not json_files:
            result['errors'].append(f"No JSON files found in: {json_dir}")
            result['valid'] = False
        else:
            result['json_files'] = json_files

            # Validate JSON files are parseable
            invalid_json = []
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    invalid_json.append(f"{json_file.name}: {str(e)}")
                except Exception as e:
                    invalid_json.append(f"{json_file.name}: {str(e)}")

            if invalid_json:
                result['errors'].append(
                    f"Invalid JSON files found:\n  " + "\n  ".join(invalid_json)
                )
                result['valid'] = False

    # Validate template_path
    if not template_path.exists():
        result['errors'].append(f"Template file does not exist: {template_path}")
        result['valid'] = False
    elif not template_path.is_file():
        result['errors'].append(f"Template path is not a file: {template_path}")
        result['valid'] = False
    elif template_path.suffix not in required_extensions:
        result['errors'].append(
            f"Template has invalid extension: {template_path.suffix} "
            f"(expected: {', '.join(required_extensions)})"
        )
        result['valid'] = False
    else:
        # Compute template hash for tracking
        try:
            with open(template_path, 'rb') as f:
                template_hash = hashlib.sha256(f.read()).hexdigest()
                result['template_hash'] = f"sha256:{template_hash[:16]}"
        except Exception as e:
            result['warnings'].append(f"Could not compute template hash: {e}")

    return result


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1m 23s", "45s", "2h 15m")

    Examples:
        >>> format_duration(45.3)
        '45s'
        >>> format_duration(95.8)
        '1m 36s'
        >>> format_duration(7325.0)
        '2h 2m 5s'
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {secs}s"

    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m {secs}s"


def create_filename_from_data(
    data: Dict[str, any],
    card_id: Optional[str] = None,
    name_field: Optional[str] = None
) -> str:
    """
    Generate a descriptive filename from JSON data.

    Attempts to extract meaningful identifier from data:
        1. Use card_id if provided
        2. Use data[name_field] if name_field provided
        3. Use data['nome'] or data['name']
        4. Use data['id']
        5. Fall back to 'document'

    Args:
        data: JSON data dictionary
        card_id: Optional card ID override
        name_field: Optional field name to use for naming

    Returns:
        Sanitized filename base (without extension)

    Examples:
        >>> create_filename_from_data({'nome': 'João Silva'}, card_id='123')
        '123_Joao_Silva'
        >>> create_filename_from_data({'name': 'Maria Santos'})
        'Maria_Santos'
    """
    parts = []

    # Add card_id if provided
    if card_id:
        parts.append(str(card_id))

    # Try to extract name
    name = None
    if name_field and name_field in data:
        name = data[name_field]
    elif 'nome' in data:
        name = data['nome']
    elif 'name' in data:
        name = data['name']
    elif 'id' in data:
        name = data['id']

    if name:
        parts.append(str(name))

    # Fall back to generic name
    if not parts:
        parts.append('document')

    filename = '_'.join(parts)
    return sanitize_filename(filename)

"""
Batch document processing engine for high-performance legal document generation.

Features:
    - Multiprocessing for parallel rendering (configurable workers)
    - Checkpoint/resume support for fault tolerance
    - Dry-run validation mode
    - Streaming ZIP creation (memory-efficient)
    - Comprehensive error reporting
    - Progress tracking with tqdm
"""

import json
import os
import zipfile
from copy import deepcopy
from datetime import datetime
from functools import partial
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Dict, List, Optional
import traceback

from tqdm import tqdm

from .engine import DocumentEngine
from .batch_utils import (
    sanitize_filename,
    estimate_batch_time,
    validate_batch_input,
    format_duration,
    create_filename_from_data
)


class BatchProcessor:
    """
    High-performance batch document processor using multiprocessing.

    Features:
        - Parallel rendering with worker pool
        - Template pre-loading and caching
        - Checkpoint/resume for fault tolerance
        - Dry-run validation mode
        - Comprehensive error tracking
        - ZIP output with streaming

    Usage:
        processor = BatchProcessor(max_workers=8)
        results = processor.process_batch(
            json_files=[Path('card_1.json'), ...],
            template_path=Path('template.docx'),
            output_dir=Path('output/')
        )
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        auto_normalize: bool = True,
        checkpoint_enabled: bool = True
    ):
        """
        Initialize batch processor.

        Args:
            max_workers: Number of parallel workers (default: min(8, cpu_count()))
            auto_normalize: Enable automatic text normalization
            checkpoint_enabled: Enable checkpoint/resume functionality
        """
        if max_workers is None:
            # Auto-tune: use cpu_count but cap at 8 for optimal performance
            max_workers = min(8, cpu_count())

        self.max_workers = max_workers
        self.auto_normalize = auto_normalize
        self.checkpoint_enabled = checkpoint_enabled

    def process_batch(
        self,
        json_files: List[Path],
        template_path: Path,
        output_dir: Path,
        create_zip: bool = True,
        zip_name: Optional[str] = None,
        name_field: Optional[str] = None,
        field_types: Optional[Dict[str, str]] = None,
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Process a batch of JSON files into documents.

        Args:
            json_files: List of JSON file paths to process
            template_path: Path to .docx template
            output_dir: Directory for output files
            create_zip: Create ZIP archive of outputs (default: True)
            zip_name: Custom ZIP filename (default: auto-generated)
            name_field: JSON field to use for output filenames
            field_types: Optional normalization type mapping
            resume: Resume from checkpoint if exists (default: True)

        Returns:
            Dictionary with processing results:
                {
                    'timestamp': ISO timestamp,
                    'template_hash': Template hash,
                    'total': Total files,
                    'success': Successful renders,
                    'failed': Failed renders,
                    'skipped': Skipped (from checkpoint),
                    'duration_seconds': Processing time,
                    'workers': Number of workers used,
                    'outputs': List of output paths,
                    'errors': List of error details,
                    'zip_path': Path to ZIP (if created)
                }
        """
        start_time = datetime.now()

        # Ensure output directory exists
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Checkpoint management
        checkpoint_file = output_dir / '.checkpoint.json'
        processed_files = set()

        if resume and self.checkpoint_enabled and checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                    processed_files = set(checkpoint.get('processed', []))
                    print(f"Resuming from checkpoint: {len(processed_files)} files already processed")
            except Exception as e:
                print(f"Warning: Could not load checkpoint: {e}")

        # Filter out already processed files
        files_to_process = [f for f in json_files if str(f) not in processed_files]
        skipped_count = len(json_files) - len(files_to_process)

        if not files_to_process:
            print("All files already processed!")
            return self._create_result_summary(
                start_time=start_time,
                template_path=template_path,
                total=len(json_files),
                success=skipped_count,
                failed=0,
                skipped=skipped_count,
                outputs=[],
                errors=[]
            )

        # Prepare worker arguments
        worker_fn = partial(
            _process_single_document,
            template_path=template_path,
            output_dir=output_dir,
            auto_normalize=self.auto_normalize,
            name_field=name_field,
            field_types=field_types
        )

        # Process with multiprocessing
        print(f"Processing {len(files_to_process)} documents with {self.max_workers} workers...")

        outputs = []
        errors = []

        with Pool(processes=self.max_workers) as pool:
            results = list(
                tqdm(
                    pool.imap(worker_fn, files_to_process),
                    total=len(files_to_process),
                    desc="Rendering documents",
                    unit="doc"
                )
            )

        # Collect results and update checkpoint
        for result in results:
            if result['status'] == 'success':
                outputs.append(result['output_path'])
                processed_files.add(result['json_file'])

                # Update checkpoint after each success
                if self.checkpoint_enabled:
                    self._update_checkpoint(checkpoint_file, processed_files)
            else:
                errors.append({
                    'json_file': result['json_file'],
                    'error_type': result.get('error_type', 'Unknown'),
                    'message': result.get('message', 'Unknown error'),
                    'traceback': result.get('traceback', '')
                })

        # Create ZIP archive if requested
        zip_path = None
        if create_zip and outputs:
            zip_path = self._create_zip_archive(
                output_files=outputs,
                output_dir=output_dir,
                zip_name=zip_name,
                template_path=template_path
            )

        # Clean up checkpoint on completion
        if self.checkpoint_enabled and checkpoint_file.exists():
            checkpoint_file.unlink()

        # Generate result summary
        success_count = len(outputs)
        failed_count = len(errors)

        result_summary = self._create_result_summary(
            start_time=start_time,
            template_path=template_path,
            total=len(json_files),
            success=success_count,
            failed=failed_count,
            skipped=skipped_count,
            outputs=outputs,
            errors=errors,
            zip_path=zip_path
        )

        # Write reports
        self._write_report(output_dir / 'report.json', result_summary)
        if errors:
            self._write_errors(output_dir / 'errors.json', errors)

        return result_summary

    def validate_batch(
        self,
        json_files: List[Path],
        template_path: Path
    ) -> Dict[str, Any]:
        """
        Dry-run validation of all JSON files against template.

        Validates each JSON file can be:
            1. Parsed successfully
            2. Loaded without errors
            3. Mapped to template variables

        Does NOT render documents - only validation.

        Args:
            json_files: List of JSON file paths
            template_path: Path to .docx template

        Returns:
            Validation results:
                {
                    'valid': bool (all files valid),
                    'total': int,
                    'valid_count': int,
                    'invalid_count': int,
                    'errors': List[dict],
                    'template_variables': List[str]
                }
        """
        print(f"Validating {len(json_files)} files (dry-run mode)...")

        engine = DocumentEngine(auto_normalize=self.auto_normalize)

        # Get template variables
        try:
            template_vars = engine.get_template_variables(template_path)
        except Exception as e:
            return {
                'valid': False,
                'total': len(json_files),
                'valid_count': 0,
                'invalid_count': len(json_files),
                'errors': [{
                    'json_file': 'template',
                    'error_type': 'TemplateError',
                    'message': str(e)
                }],
                'template_variables': []
            }

        errors = []
        valid_count = 0

        for json_file in tqdm(json_files, desc="Validating", unit="file"):
            try:
                # Load JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate against template
                validation = engine.validate_data(template_path, data)

                # Report missing fields as errors
                if validation['missing']:
                    errors.append({
                        'json_file': str(json_file),
                        'error_type': 'ValidationError',
                        'message': f"Missing required fields: {', '.join(validation['missing'])}",
                        'missing_fields': validation['missing']
                    })
                else:
                    valid_count += 1

            except json.JSONDecodeError as e:
                errors.append({
                    'json_file': str(json_file),
                    'error_type': 'JSONDecodeError',
                    'message': str(e)
                })
            except Exception as e:
                errors.append({
                    'json_file': str(json_file),
                    'error_type': type(e).__name__,
                    'message': str(e)
                })

        invalid_count = len(json_files) - valid_count
        all_valid = invalid_count == 0

        return {
            'valid': all_valid,
            'total': len(json_files),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'errors': errors,
            'template_variables': template_vars
        }

    def _update_checkpoint(self, checkpoint_file: Path, processed_files: set) -> None:
        """Update checkpoint file with processed files."""
        try:
            checkpoint = {
                'timestamp': datetime.now().isoformat(),
                'processed': sorted(list(processed_files))
            }
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update checkpoint: {e}")

    def _create_zip_archive(
        self,
        output_files: List[Path],
        output_dir: Path,
        zip_name: Optional[str],
        template_path: Path
    ) -> Path:
        """
        Create ZIP archive of output files with streaming.

        Args:
            output_files: List of output file paths
            output_dir: Output directory
            zip_name: Custom ZIP name or None for auto-generated
            template_path: Template path (for naming)

        Returns:
            Path to created ZIP file
        """
        if zip_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            template_name = template_path.stem
            zip_name = f"{template_name}_{timestamp}.zip"

        zip_path = output_dir / zip_name

        print(f"Creating ZIP archive: {zip_path.name}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for output_file in tqdm(output_files, desc="Archiving", unit="file"):
                # Use relative path in ZIP (just filename)
                arcname = output_file.name
                zf.write(output_file, arcname=arcname)

        return zip_path

    def _create_result_summary(
        self,
        start_time: datetime,
        template_path: Path,
        total: int,
        success: int,
        failed: int,
        skipped: int,
        outputs: List[Path],
        errors: List[Dict],
        zip_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create result summary dictionary."""
        duration = (datetime.now() - start_time).total_seconds()

        # Compute template hash
        import hashlib
        try:
            with open(template_path, 'rb') as f:
                template_hash = hashlib.sha256(f.read()).hexdigest()
                template_hash_short = f"sha256:{template_hash[:16]}"
        except:
            template_hash_short = "unknown"

        summary = {
            'timestamp': start_time.isoformat(),
            'template_hash': template_hash_short,
            'template_name': template_path.name,
            'total': total,
            'success': success,
            'failed': failed,
            'skipped': skipped,
            'duration_seconds': round(duration, 2),
            'duration_formatted': format_duration(duration),
            'workers': self.max_workers,
            'outputs': [str(p) for p in outputs],
            'errors': errors
        }

        if zip_path:
            summary['zip_path'] = str(zip_path)

        return summary

    def _write_report(self, report_path: Path, summary: Dict[str, Any]) -> None:
        """Write summary report to JSON file."""
        # Remove outputs list from report (can be large)
        report_data = {k: v for k, v in summary.items() if k != 'outputs'}
        report_data['output_count'] = len(summary['outputs'])

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"Report written to: {report_path}")

    def _write_errors(self, errors_path: Path, errors: List[Dict]) -> None:
        """Write errors to JSON file."""
        error_data = {
            'error_count': len(errors),
            'errors': errors
        }

        with open(errors_path, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)

        print(f"Errors written to: {errors_path}")


# === WORKER FUNCTION (must be at module level for multiprocessing) ===

def _process_single_document(
    json_path: Path,
    template_path: Path,
    output_dir: Path,
    auto_normalize: bool,
    name_field: Optional[str],
    field_types: Optional[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Worker function to process a single document.

    This function runs in a separate process and must be isolated.
    Returns result dict instead of raising exceptions.

    Args:
        json_path: Path to JSON file
        template_path: Path to template
        output_dir: Output directory
        auto_normalize: Enable normalization
        name_field: Field for filename
        field_types: Normalization types

    Returns:
        Result dictionary:
            {
                'status': 'success' | 'error',
                'json_file': str,
                'output_path': Path (if success),
                'error_type': str (if error),
                'message': str (if error),
                'traceback': str (if error)
            }
    """
    try:
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Generate output filename
        # Try to extract card_id from filename (e.g., "card_123.json" → "123")
        card_id = None
        if json_path.stem.startswith('card_'):
            card_id = json_path.stem.replace('card_', '')

        filename_base = create_filename_from_data(
            data=data,
            card_id=card_id,
            name_field=name_field
        )

        output_path = output_dir / f"{filename_base}.docx"

        # Handle filename conflicts
        counter = 1
        while output_path.exists():
            output_path = output_dir / f"{filename_base}_{counter}.docx"
            counter += 1

        # Render document
        engine = DocumentEngine(auto_normalize=auto_normalize)
        engine.render(
            template_path=template_path,
            data=data,
            output_path=output_path,
            field_types=field_types
        )

        return {
            'status': 'success',
            'json_file': str(json_path),
            'output_path': output_path
        }

    except json.JSONDecodeError as e:
        return {
            'status': 'error',
            'json_file': str(json_path),
            'error_type': 'JSONDecodeError',
            'message': f"Invalid JSON: {str(e)}",
            'traceback': traceback.format_exc()
        }

    except FileNotFoundError as e:
        return {
            'status': 'error',
            'json_file': str(json_path),
            'error_type': 'FileNotFoundError',
            'message': str(e),
            'traceback': traceback.format_exc()
        }

    except Exception as e:
        return {
            'status': 'error',
            'json_file': str(json_path),
            'error_type': type(e).__name__,
            'message': str(e),
            'traceback': traceback.format_exc()
        }

#!/usr/bin/env python3
"""
Batch Document Assembler CLI

Command-line interface for high-performance batch processing of legal documents.

Usage:
    # Basic batch processing
    python batch_cli.py --input-dir json_inputs/ --template template.docx --output-dir output/

    # With custom worker count
    python batch_cli.py --input-dir json/ --template tpl.docx --output-dir out/ --workers 16

    # Dry-run validation only
    python batch_cli.py --input-dir json/ --template tpl.docx --dry-run

    # No ZIP creation (individual files only)
    python batch_cli.py --input-dir json/ --template tpl.docx --output-dir out/ --no-zip

    # Custom ZIP name
    python batch_cli.py --input-dir json/ --template tpl.docx --output-dir out/ --zip-name results.zip

    # Disable checkpoint/resume
    python batch_cli.py --input-dir json/ --template tpl.docx --output-dir out/ --no-checkpoint
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.batch_engine import BatchProcessor
from src.batch_utils import (
    validate_batch_input,
    estimate_batch_time,
    format_duration
)


console = Console()


def print_validation_results(validation: dict) -> None:
    """Print formatted validation results."""
    if validation['valid']:
        console.print(Panel(
            "[green]✓ All validation checks passed![/green]",
            title="Validation Results",
            border_style="green"
        ))

        # Show summary
        table = Table(title="Batch Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")

        table.add_row("JSON Files", str(len(validation['json_files'])))
        table.add_row("Template", validation['template_hash'] or "N/A")

        console.print(table)
    else:
        console.print(Panel(
            "[red]✗ Validation failed![/red]",
            title="Validation Results",
            border_style="red"
        ))

        # Show errors
        for error in validation['errors']:
            console.print(f"[red]• {error}[/red]")

        if validation['warnings']:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in validation['warnings']:
                console.print(f"[yellow]• {warning}[/yellow]")


def print_dry_run_results(results: dict) -> None:
    """Print formatted dry-run validation results."""
    if results['valid']:
        console.print(Panel(
            f"[green]✓ All {results['valid_count']} files are valid![/green]",
            title="Dry-Run Validation",
            border_style="green"
        ))

        # Show template variables
        if results['template_variables']:
            console.print("\n[cyan]Template Variables:[/cyan]")
            for var in results['template_variables']:
                console.print(f"  • {var}")
    else:
        console.print(Panel(
            f"[red]✗ {results['invalid_count']} of {results['total']} files have errors![/red]",
            title="Dry-Run Validation",
            border_style="red"
        ))

        # Show errors in table
        table = Table(title="Validation Errors")
        table.add_column("File", style="cyan")
        table.add_column("Error Type", style="yellow")
        table.add_column("Message", style="red")

        for error in results['errors']:
            json_file = Path(error['json_file']).name
            table.add_row(
                json_file,
                error['error_type'],
                error['message']
            )

        console.print(table)


def print_processing_results(results: dict) -> None:
    """Print formatted processing results."""
    success = results['success']
    failed = results['failed']
    total = results['total']

    # Status panel
    if failed == 0:
        status_msg = f"[green]✓ Successfully processed all {success} documents![/green]"
        border_style = "green"
    elif success > 0:
        status_msg = f"[yellow]⚠ Processed {success} documents, {failed} failed[/yellow]"
        border_style = "yellow"
    else:
        status_msg = f"[red]✗ All {failed} documents failed![/red]"
        border_style = "red"

    console.print(Panel(status_msg, title="Processing Results", border_style=border_style))

    # Summary table
    table = Table(title="Batch Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")

    table.add_row("Total Files", str(total))
    table.add_row("Success", f"[green]{success}[/green]")
    table.add_row("Failed", f"[red]{failed}[/red]" if failed > 0 else "0")
    if results.get('skipped', 0) > 0:
        table.add_row("Skipped (checkpoint)", str(results['skipped']))
    table.add_row("Duration", results['duration_formatted'])
    table.add_row("Workers", str(results['workers']))
    table.add_row("Template", results['template_name'])

    console.print(table)

    # ZIP path if created
    if 'zip_path' in results:
        console.print(f"\n[green]📦 ZIP archive:[/green] {results['zip_path']}")

    # Error summary
    if failed > 0:
        console.print(f"\n[red]Errors:[/red] See errors.json for details")

        # Show first few errors
        for error in results['errors'][:3]:
            json_file = Path(error['json_file']).name
            console.print(f"  • {json_file}: {error['message']}")

        if len(results['errors']) > 3:
            console.print(f"  ... and {len(results['errors']) - 3} more errors")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch legal document assembler - high-performance rendering engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s --input-dir json_inputs/ --template template.docx --output-dir output/

  # Validation only (dry-run)
  %(prog)s --input-dir json/ --template template.docx --dry-run

  # Custom worker count
  %(prog)s --input-dir json/ --template tpl.docx --output-dir out/ --workers 16

  # No ZIP creation
  %(prog)s --input-dir json/ --template tpl.docx --output-dir out/ --no-zip
        """
    )

    # Required arguments
    parser.add_argument(
        '--input-dir',
        type=Path,
        required=True,
        help='Directory containing JSON input files'
    )
    parser.add_argument(
        '--template',
        type=Path,
        required=True,
        help='Path to .docx template file'
    )

    # Optional arguments
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output'),
        help='Output directory for generated documents (default: output/)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: auto-detected, max 8)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validation only - do not generate documents'
    )
    parser.add_argument(
        '--no-zip',
        action='store_true',
        help='Do not create ZIP archive of outputs'
    )
    parser.add_argument(
        '--zip-name',
        type=str,
        default=None,
        help='Custom ZIP filename (default: auto-generated)'
    )
    parser.add_argument(
        '--no-checkpoint',
        action='store_true',
        help='Disable checkpoint/resume functionality'
    )
    parser.add_argument(
        '--name-field',
        type=str,
        default=None,
        help='JSON field to use for output filenames (default: auto-detect)'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Do not resume from checkpoint (start fresh)'
    )

    args = parser.parse_args()

    # Print header
    console.print(Panel(
        "[bold cyan]Legal Document Batch Assembler[/bold cyan]\n"
        "High-performance parallel document generation",
        border_style="cyan"
    ))

    # Pre-flight validation
    console.print("\n[cyan]Step 1:[/cyan] Validating batch input...")
    validation = validate_batch_input(
        json_dir=args.input_dir,
        template_path=args.template
    )

    print_validation_results(validation)

    if not validation['valid']:
        console.print("\n[red]Aborting due to validation errors.[/red]")
        sys.exit(1)

    json_files = validation['json_files']

    # Estimate processing time
    estimated_time = estimate_batch_time(
        num_docs=len(json_files),
        workers=args.workers or 8
    )
    console.print(
        f"\n[cyan]Estimated processing time:[/cyan] {format_duration(estimated_time)}"
    )

    # Dry-run mode
    if args.dry_run:
        console.print("\n[cyan]Step 2:[/cyan] Running dry-run validation...")
        processor = BatchProcessor(
            max_workers=args.workers,
            checkpoint_enabled=not args.no_checkpoint
        )
        results = processor.validate_batch(
            json_files=json_files,
            template_path=args.template
        )
        print_dry_run_results(results)

        if results['valid']:
            console.print("\n[green]✓ Dry-run complete - all files are valid![/green]")
            sys.exit(0)
        else:
            console.print("\n[red]✗ Dry-run failed - fix errors before processing.[/red]")
            sys.exit(1)

    # Process batch
    console.print("\n[cyan]Step 2:[/cyan] Processing batch...")
    processor = BatchProcessor(
        max_workers=args.workers,
        checkpoint_enabled=not args.no_checkpoint
    )

    try:
        results = processor.process_batch(
            json_files=json_files,
            template_path=args.template,
            output_dir=args.output_dir,
            create_zip=not args.no_zip,
            zip_name=args.zip_name,
            name_field=args.name_field,
            resume=not args.no_resume
        )

        print_processing_results(results)

        if results['failed'] > 0:
            console.print(f"\n[yellow]⚠ Completed with errors. Check {args.output_dir}/errors.json[/yellow]")
            sys.exit(1)
        else:
            console.print(f"\n[green]✓ All documents generated successfully![/green]")
            console.print(f"[cyan]Output directory:[/cyan] {args.output_dir}")
            sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ Processing interrupted by user.[/yellow]")
        if not args.no_checkpoint:
            console.print("[cyan]Progress saved to checkpoint. Use --no-resume to start fresh.[/cyan]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]✗ Fatal error:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

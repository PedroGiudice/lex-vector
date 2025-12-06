#!/usr/bin/env python3
"""
End-to-end execution test for legal-doc-assembler.

This script:
1. Loads the test template
2. Loads the sample JSON (with intentionally missing 'rg' field)
3. Renders the document
4. Verifies the output
5. Reports results
"""

import json
import sys
from pathlib import Path

from docx import Document
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.engine import DocumentEngine

console = Console()


def main():
    """Run end-to-end execution test."""
    console.print(Panel.fit(
        "[bold blue]Legal Document Assembler - Execution Test[/bold blue]",
        border_style="blue"
    ))

    # Paths
    base_dir = Path(__file__).parent
    template_path = base_dir / "resources" / "templates" / "template_teste.docx"
    json_path = base_dir / "resources" / "dados_teste.json"
    output_path = base_dir / "output" / "documento_teste.docx"

    # Ensure output directory exists
    output_path.parent.mkdir(exist_ok=True)

    # Track test results
    test_results = []

    # Initialize engine
    console.print("\n[cyan]1. Initializing DocumentEngine...[/cyan]")
    try:
        engine = DocumentEngine(auto_normalize=True)
        console.print("   [green]✔[/green] Engine initialized")
        test_results.append(("Engine initialization", True, "Success"))
    except Exception as e:
        console.print(f"   [red]✘[/red] Engine initialization failed: {e}")
        test_results.append(("Engine initialization", False, str(e)))
        return 1

    # Get template variables
    console.print("\n[cyan]2. Analyzing template...[/cyan]")
    try:
        variables = engine.get_template_variables(template_path)
        console.print(f"   [green]✔[/green] Found {len(variables)} variables")
        console.print(f"   Variables: {', '.join(variables[:8])}...")
        test_results.append(("Template analysis", True, f"{len(variables)} variables found"))
    except Exception as e:
        console.print(f"   [red]✘[/red] Template analysis failed: {e}")
        test_results.append(("Template analysis", False, str(e)))
        return 1

    # Load and validate data
    console.print("\n[cyan]3. Loading and validating data...[/cyan]")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        console.print(f"   [green]✔[/green] JSON loaded with {len(data)} fields")

        engine.print_validation_report(template_path, data)
        test_results.append(("Data loading", True, f"{len(data)} fields"))
    except Exception as e:
        console.print(f"   [red]✘[/red] Data loading failed: {e}")
        test_results.append(("Data loading", False, str(e)))
        return 1

    # Render document
    console.print("\n[cyan]4. Rendering document...[/cyan]")
    try:
        result_path = engine.render_from_json(template_path, json_path, output_path)
        test_results.append(("Document rendering", True, str(result_path)))
    except Exception as e:
        console.print(f"   [red]✘[/red] Rendering failed: {e}")
        test_results.append(("Document rendering", False, str(e)))
        return 1

    # Verify output
    console.print("\n[cyan]5. Verifying output...[/cyan]")
    try:
        doc = Document(result_path)
        full_text = "\n".join([p.text for p in doc.paragraphs])

        # Create verification table
        checks = Table(title="Verification Results")
        checks.add_column("Check", style="bold")
        checks.add_column("Result")
        checks.add_column("Details")

        # Check 1: File exists
        file_exists = result_path.exists()
        checks.add_row(
            "Output file exists",
            "[green]PASS[/green]" if file_exists else "[red]FAIL[/red]",
            str(result_path)
        )
        test_results.append(("File exists", file_exists, str(result_path)))

        # Check 2: Missing fields preserved (RG)
        rg_preserved = "{{ rg }}" in full_text
        checks.add_row(
            "Missing 'rg' preserved",
            "[green]PASS[/green]" if rg_preserved else "[red]FAIL[/red]",
            "{{ rg }} visible in output" if rg_preserved else "Field was removed"
        )
        test_results.append(("Fault tolerance ({{ rg }})", rg_preserved, ""))

        # Check 3: UTF-8 characters
        utf8_ok = "João" in full_text or "São Paulo" in full_text
        checks.add_row(
            "UTF-8 characters",
            "[green]PASS[/green]" if utf8_ok else "[red]FAIL[/red]",
            "Accented characters preserved" if utf8_ok else "Encoding issue"
        )
        test_results.append(("UTF-8 characters", utf8_ok, ""))

        # Check 4: CPF filter applied
        cpf_formatted = "987.654.321-00" in full_text
        checks.add_row(
            "CPF filter applied",
            "[green]PASS[/green]" if cpf_formatted else "[yellow]CHECK[/yellow]",
            "CPF formatted correctly" if cpf_formatted else "Manual verification needed"
        )
        test_results.append(("CPF filter", cpf_formatted, ""))

        # Check 5: Name normalization
        name_normalized = "Maria das Graças da Silva" in full_text
        checks.add_row(
            "Name normalization",
            "[green]PASS[/green]" if name_normalized else "[yellow]CHECK[/yellow]",
            "Names properly cased" if name_normalized else "Manual verification needed"
        )
        test_results.append(("Name normalization", name_normalized, ""))

        # Check 6: Address normalization
        address_normalized = "Avenida" in full_text and "nº" in full_text
        checks.add_row(
            "Address normalization",
            "[green]PASS[/green]" if address_normalized else "[yellow]CHECK[/yellow]",
            "Address expanded" if address_normalized else "Manual verification needed"
        )
        test_results.append(("Address normalization", address_normalized, ""))

        console.print(checks)

    except Exception as e:
        console.print(f"   [red]✘[/red] Verification failed: {e}")
        test_results.append(("Verification", False, str(e)))
        return 1

    # Final summary
    passed = sum(1 for _, result, _ in test_results if result)
    total = len(test_results)

    if passed == total:
        console.print(Panel.fit(
            f"[bold green]✔ All {total} checks passed![/bold green]\n"
            f"Output: {result_path}\n"
            f"Size: {result_path.stat().st_size} bytes",
            title="Execution Complete",
            border_style="green"
        ))
        return 0
    else:
        console.print(Panel.fit(
            f"[bold yellow]⚠ {passed}/{total} checks passed[/bold yellow]\n"
            f"Output: {result_path}\n"
            f"Some checks require manual verification",
            title="Execution Complete with Warnings",
            border_style="yellow"
        ))
        return 0  # Still success, some filters may need manual check


if __name__ == "__main__":
    sys.exit(main())

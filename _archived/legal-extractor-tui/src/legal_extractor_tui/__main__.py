"""CLI entry point for Legal Extractor TUI."""

import argparse
import sys

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Legal Extractor TUI - Extract text from Brazilian legal PDFs"
    )
    parser.add_argument(
        "--theme",
        choices=["neon", "matrix", "synthwave", "dark"],
        default="neon",
        help="Color theme (default: neon)"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Enable development mode with DevTools"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="PDF file to process on startup (optional)"
    )

    args = parser.parse_args()

    # Map short theme names to full names
    theme_map = {
        "neon": "vibe-neon",
        "matrix": "vibe-matrix",
        "synthwave": "vibe-synthwave",
        "dark": "minimal-dark",
    }

    from legal_extractor_tui.app import LegalExtractorApp

    app = LegalExtractorApp(
        theme_name=theme_map[args.theme],
        dev_mode=args.dev,
        initial_file=args.file
    )
    app.run()

    return 0

if __name__ == "__main__":
    sys.exit(main())

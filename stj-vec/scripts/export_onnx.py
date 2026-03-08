#!/usr/bin/env python3
"""Exporta BGE-M3 para ONNX via optimum."""
from optimum.exporters.onnx import main_export
from pathlib import Path

OUTPUT_DIR = Path("models/bge-m3-onnx")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

main_export(
    "BAAI/bge-m3",
    str(OUTPUT_DIR),
    task="feature-extraction",
    opset=17,
)

print(f"Modelo exportado em {OUTPUT_DIR}")
for f in sorted(OUTPUT_DIR.iterdir()):
    size_mb = f.stat().st_size / 1024 / 1024
    print(f"  {f.name}: {size_mb:.1f} MB")

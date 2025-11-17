#!/usr/bin/env python3
"""Teste rápido do download corrigido"""
import json
from pathlib import Path
from src import ContinuousDownloader
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Config mínima
config = {
    "tribunais": {"modo": "all", "prioritarios": [], "excluidos": []},
    "download": {"intervalo_minutos": 30, "max_workers": 10, "timeout_seconds": 60},
    "rate_limiting": {
        "requests_per_minute": 30,
        "delay_between_requests_seconds": 2,
        "backoff_on_429": True,
        "max_backoff_seconds": 300
    },
    "scraping": {"user_agent": "Mozilla/5.0"},
    "paths": {
        "data_root": "temp_quick_test",
        "cadernos": "cadernos",
        "logs": "logs",
        "cache": "cache",
        "checkpoint": "checkpoint.json"
    }
}

downloader = ContinuousDownloader(config)

print("\n🧪 Testando download de TJSP 2025-11-14 (sabemos que existe)")
resultado = downloader.run_once(data="2025-11-14", parallel=False)

print(f"\n✅ Sucessos: {resultado['sucessos']}")
print(f"❌ Falhas: {resultado['falhas']}")

if resultado['sucessos'] > 0:
    print("\n🎉 DOWNLOAD FUNCIONAL! Bug corrigido!")
else:
    print("\n⚠️  Ainda sem downloads (investigar)")

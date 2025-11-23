#!/usr/bin/env python3
"""
DJEN API Performance Diagnostic Tool

Usage:
    python diagnostic.py --tribunal STJ --data 2025-11-20 --profile
    python diagnostic.py --help

Identifies performance bottlenecks in DJEN API integration:
- API latency (network)
- HTML parsing time
- Database write speed
- Rate limiting delays
"""

import argparse
import time
import cProfile
import pstats
import io
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import sqlite3
import hashlib
from datetime import datetime

BASE_URL = "https://comunicaapi.pje.jus.br"


class PerformanceDiagnostic:
    def __init__(self, tribunal: str, data: str):
        self.tribunal = tribunal
        self.data = data
        self.metrics = {}

    def measure_api_latency(self, num_requests=10) -> Dict:
        """Measures API response time"""
        print(f"\n📊 Measuring API latency ({num_requests} requests)...")

        latencies = []
        for i in range(num_requests):
            start = time.time()
            try:
                response = requests.get(
                    f"{BASE_URL}/api/v1/comunicacao",
                    params={
                        'siglaTribunal': self.tribunal,
                        'dataInicio': self.data,
                        'dataFim': self.data,
                        'page': i + 1,
                        'limit': 10
                    },
                    timeout=30
                )
                elapsed = time.time() - start
                latencies.append(elapsed)
                print(f"  Request {i+1}: {elapsed:.3f}s ({response.status_code})")
            except Exception as e:
                print(f"  Request {i+1}: ERROR - {e}")

        if not latencies:
            return {'error': 'No successful requests'}

        return {
            'min': min(latencies),
            'max': max(latencies),
            'avg': sum(latencies) / len(latencies),
            'p95': sorted(latencies)[int(len(latencies) * 0.95)],
            'total_time': sum(latencies)
        }

    def measure_html_parsing(self, num_samples=100) -> Dict:
        """Measures HTML parsing performance"""
        print(f"\n📊 Measuring HTML parsing ({num_samples} samples)...")

        # Fetch sample data
        response = requests.get(
            f"{BASE_URL}/api/v1/comunicacao",
            params={
                'siglaTribunal': self.tribunal,
                'dataInicio': self.data,
                'dataFim': self.data,
                'limit': num_samples
            }
        )

        items = response.json().get('items', [])[:num_samples]
        if not items:
            return {'error': 'No items found'}

        parse_times = []
        for item in items:
            texto_html = item.get('texto', '')
            start = time.time()
            soup = BeautifulSoup(texto_html, 'html.parser')
            texto_limpo = soup.get_text(separator='\n', strip=True)
            elapsed = time.time() - start
            parse_times.append(elapsed)

        return {
            'min': min(parse_times),
            'max': max(parse_times),
            'avg': sum(parse_times) / len(parse_times),
            'total_time': sum(parse_times),
            'throughput': len(parse_times) / sum(parse_times)
        }

    def measure_database_writes(self, num_writes=1000) -> Dict:
        """Measures database write performance"""
        print(f"\n📊 Measuring database writes ({num_writes} writes)...")

        # Create in-memory database for testing
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()

        # Create schema
        cursor.execute("""
        CREATE TABLE publicacoes (
            id TEXT PRIMARY KEY,
            hash_conteudo TEXT NOT NULL UNIQUE,
            tribunal TEXT NOT NULL,
            texto_html TEXT NOT NULL,
            data_publicacao TEXT NOT NULL
        )
        """)

        # Measure individual commits
        print("  Testing individual commits...")
        start = time.time()
        for i in range(100):
            cursor.execute("""
            INSERT INTO publicacoes (id, hash_conteudo, tribunal, texto_html, data_publicacao)
            VALUES (?, ?, ?, ?, ?)
            """, (f"id_{i}", f"hash_{i}", self.tribunal, "test text", self.data))
            conn.commit()
        individual_time = time.time() - start
        individual_rate = 100 / individual_time

        # Clear table
        cursor.execute("DELETE FROM publicacoes")

        # Measure batch commits (100 per batch)
        print("  Testing batch commits (100/batch)...")
        start = time.time()
        for i in range(num_writes):
            cursor.execute("""
            INSERT INTO publicacoes (id, hash_conteudo, tribunal, texto_html, data_publicacao)
            VALUES (?, ?, ?, ?, ?)
            """, (f"id_batch_{i}", f"hash_batch_{i}", self.tribunal, "test text", self.data))
            if (i + 1) % 100 == 0:
                conn.commit()
        conn.commit()
        batch_time = time.time() - start
        batch_rate = num_writes / batch_time

        conn.close()

        speedup = batch_rate / individual_rate

        return {
            'individual_commits': {
                'time': individual_time,
                'rate': individual_rate
            },
            'batch_commits': {
                'time': batch_time,
                'rate': batch_rate
            },
            'speedup': speedup
        }

    def run_full_diagnostic(self):
        """Runs complete diagnostic suite"""
        print(f"🔍 DJEN API Performance Diagnostic")
        print(f"=" * 60)
        print(f"Tribunal: {self.tribunal}")
        print(f"Date: {self.data}")
        print(f"Timestamp: {datetime.now()}")
        print(f"=" * 60)

        # API latency
        api_metrics = self.measure_api_latency(10)
        self.metrics['api'] = api_metrics

        # HTML parsing
        parsing_metrics = self.measure_html_parsing(100)
        self.metrics['parsing'] = parsing_metrics

        # Database writes
        db_metrics = self.measure_database_writes(1000)
        self.metrics['database'] = db_metrics

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Prints diagnostic summary"""
        print(f"\n" + "=" * 60)
        print(f"📊 DIAGNOSTIC SUMMARY")
        print(f"=" * 60)

        # API
        if 'api' in self.metrics and 'avg' in self.metrics['api']:
            api = self.metrics['api']
            print(f"\n🌐 API Latency:")
            print(f"  Min:     {api['min']:.3f}s")
            print(f"  Avg:     {api['avg']:.3f}s")
            print(f"  Max:     {api['max']:.3f}s")
            print(f"  P95:     {api['p95']:.3f}s")

        # Parsing
        if 'parsing' in self.metrics and 'avg' in self.metrics['parsing']:
            parsing = self.metrics['parsing']
            print(f"\n📝 HTML Parsing:")
            print(f"  Avg:        {parsing['avg']*1000:.2f}ms")
            print(f"  Throughput: {parsing['throughput']:.1f} docs/sec")

        # Database
        if 'database' in self.metrics:
            db = self.metrics['database']
            print(f"\n💾 Database Writes:")
            print(f"  Individual commits: {db['individual_commits']['rate']:.1f} writes/sec")
            print(f"  Batch commits:      {db['batch_commits']['rate']:.1f} writes/sec")
            print(f"  Speedup:            {db['speedup']:.1f}x")

        # Bottleneck identification
        print(f"\n🎯 Bottleneck Analysis:")
        self.identify_bottlenecks()

    def identify_bottlenecks(self):
        """Identifies primary bottlenecks"""
        api_avg = self.metrics.get('api', {}).get('avg', 0)
        parsing_avg = self.metrics.get('parsing', {}).get('avg', 0)

        total_per_request = api_avg + (parsing_avg * 100)  # Assuming 100 items per page

        print(f"  Per API request ({100} items):")
        print(f"    API call:     {api_avg:.3f}s ({api_avg/total_per_request*100:.1f}%)")
        print(f"    HTML parsing: {parsing_avg*100:.3f}s ({parsing_avg*100/total_per_request*100:.1f}%)")

        if api_avg > 2.0:
            print(f"\n  ⚠️ HIGH API LATENCY - Network/API server is slow")
            print(f"     Recommendation: Reduce requests, use caching")

        if parsing_avg > 0.05:
            print(f"\n  ⚠️ SLOW HTML PARSING - Consider faster parser")
            print(f"     Recommendation: Use lxml instead of html.parser")

        db_speedup = self.metrics.get('database', {}).get('speedup', 0)
        if db_speedup > 100:
            print(f"\n  ✅ BATCH COMMITS CRITICAL - {db_speedup:.0f}x speedup available")
            print(f"     Recommendation: ALWAYS use batch commits (100/batch)")


def main():
    parser = argparse.ArgumentParser(
        description='DJEN API Performance Diagnostic Tool'
    )
    parser.add_argument(
        '--tribunal',
        default='STJ',
        help='Tribunal code (default: STJ)'
    )
    parser.add_argument(
        '--data',
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Publication date YYYY-MM-DD (default: today)'
    )
    parser.add_argument(
        '--profile',
        action='store_true',
        help='Enable cProfile profiling'
    )

    args = parser.parse_args()

    if args.profile:
        print("🔬 Running with cProfile profiling...")
        profiler = cProfile.Profile()
        profiler.enable()

    diagnostic = PerformanceDiagnostic(args.tribunal, args.data)
    diagnostic.run_full_diagnostic()

    if args.profile:
        profiler.disable()
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        print("\n" + "=" * 60)
        print("📊 PROFILING RESULTS (Top 20)")
        print("=" * 60)
        print(s.getvalue())


if __name__ == '__main__':
    main()

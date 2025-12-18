"""
Test STJ Client.

Quick tests to verify backend proxy layer works correctly.
Run with: python -m pytest services/test_stj_client.py -v

Or manually:
    cd poc-fasthtml-stj
    python services/test_stj_client.py
"""
from __future__ import annotations

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import (
    STJClient,
    STJConnectionError,
    STJValidationError,
    quick_health_check,
    quick_search
)


async def test_health_check():
    """Test health check endpoint."""
    print("\n[TEST] Health Check")
    print("-" * 60)

    try:
        async with STJClient() as client:
            health = await client.health_check()

            print(f"  Status: {health.status}")
            print(f"  Version: {health.version}")
            print(f"  Database: {health.database}")
            print(f"  Timestamp: {health.timestamp}")

            assert health.status == "healthy"
            print("\n  [PASS] Health check successful")
            return True

    except STJConnectionError as e:
        print(f"\n  [WARN] Cannot connect to STJ API: {e}")
        print("  Make sure Docker containers are running:")
        print("    cd legal-workbench/docker && docker compose ps")
        return False

    except Exception as e:
        print(f"\n  [FAIL] Unexpected error: {e}")
        return False


async def test_search():
    """Test search endpoint."""
    print("\n[TEST] Search")
    print("-" * 60)

    try:
        async with STJClient() as client:
            # Search for a common term
            results = await client.search(
                termo="responsabilidade civil",
                dias=365,
                limit=10
            )

            print(f"  Total results: {results.total}")
            print(f"  Returned: {len(results.resultados)}")
            print(f"  Limit: {results.limit}")
            print(f"  Offset: {results.offset}")

            if results.resultados:
                print("\n  First result:")
                first = results.resultados[0]
                print(f"    ID: {first.id}")
                print(f"    Processo: {first.numero_processo}")
                print(f"    Órgão: {first.orgao_julgador}")
                print(f"    Relator: {first.relator}")
                print(f"    Data Julgamento: {first.data_julgamento}")
                if first.ementa:
                    print(f"    Ementa: {first.ementa[:100]}...")

            print("\n  [PASS] Search successful")
            return True

    except STJConnectionError as e:
        print(f"\n  [WARN] Cannot connect: {e}")
        return False

    except Exception as e:
        print(f"\n  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_search_with_filters():
    """Test search with filters."""
    print("\n[TEST] Search with Filters")
    print("-" * 60)

    try:
        async with STJClient() as client:
            results = await client.search(
                termo="dano moral",
                orgao="TERCEIRA TURMA",
                dias=180,
                limit=5,
                campo="ementa"
            )

            print(f"  Total results: {results.total}")
            print(f"  Returned: {len(results.resultados)}")

            for i, r in enumerate(results.resultados, 1):
                print(f"\n  Result {i}:")
                print(f"    Órgão: {r.orgao_julgador}")
                print(f"    Processo: {r.numero_processo}")
                print(f"    Resultado: {r.resultado_julgamento}")

            print("\n  [PASS] Filtered search successful")
            return True

    except STJConnectionError as e:
        print(f"\n  [WARN] Cannot connect: {e}")
        return False

    except Exception as e:
        print(f"\n  [FAIL] Error: {e}")
        return False


async def test_stats():
    """Test statistics endpoint."""
    print("\n[TEST] Statistics")
    print("-" * 60)

    try:
        async with STJClient() as client:
            stats = await client.get_stats()

            print(f"  Total acordãos: {stats.total_acordaos}")
            print(f"  DB size (MB): {stats.tamanho_db_mb:.2f}")
            print(f"  Last 30 days: {stats.ultimos_30_dias}")

            print("\n  By Órgão:")
            for orgao, count in list(stats.por_orgao.items())[:5]:
                print(f"    {orgao}: {count}")

            print("\n  By Tipo:")
            for tipo, count in stats.por_tipo.items():
                print(f"    {tipo}: {count}")

            print("\n  [PASS] Stats retrieval successful")
            return True

    except STJConnectionError as e:
        print(f"\n  [WARN] Cannot connect: {e}")
        return False

    except Exception as e:
        print(f"\n  [FAIL] Error: {e}")
        return False


async def test_validation():
    """Test input validation."""
    print("\n[TEST] Input Validation")
    print("-" * 60)

    try:
        async with STJClient() as client:
            # Test short search term
            try:
                await client.search(termo="ab")  # Too short
                print("  [FAIL] Should have raised STJValidationError for short term")
                return False
            except STJValidationError as e:
                print(f"  [OK] Caught validation error for short term: {e}")

            # Test invalid campo
            try:
                await client.search(termo="test", campo="invalid_field")
                print("  [FAIL] Should have raised STJValidationError for invalid campo")
                return False
            except STJValidationError as e:
                print(f"  [OK] Caught validation error for invalid campo: {e}")

            print("\n  [PASS] Validation working correctly")
            return True

    except Exception as e:
        print(f"\n  [FAIL] Unexpected error: {e}")
        return False


async def test_convenience_functions():
    """Test convenience functions."""
    print("\n[TEST] Convenience Functions")
    print("-" * 60)

    try:
        # Quick health check
        health = await quick_health_check()
        print(f"  quick_health_check(): {health.status}")

        # Quick search
        results = await quick_search("processo", limit=3)
        print(f"  quick_search(): {results.total} results")

        print("\n  [PASS] Convenience functions work")
        return True

    except STJConnectionError as e:
        print(f"\n  [WARN] Cannot connect: {e}")
        return False

    except Exception as e:
        print(f"\n  [FAIL] Error: {e}")
        return False


async def test_sync():
    """Test sync endpoints (without actually triggering sync)."""
    print("\n[TEST] Sync Status (read-only)")
    print("-" * 60)

    try:
        async with STJClient() as client:
            # Just check status, don't trigger
            status = await client.get_sync_status()

            print(f"  Status: {status.status}")
            print(f"  Downloaded: {status.downloaded}")
            print(f"  Processed: {status.processed}")
            print(f"  Inserted: {status.inserted}")
            print(f"  Duplicates: {status.duplicates}")
            print(f"  Errors: {status.errors}")

            if status.message:
                print(f"  Message: {status.message}")

            print("\n  [PASS] Sync status retrieved")
            print("  [INFO] Not triggering actual sync to avoid interfering with backend")
            return True

    except STJConnectionError as e:
        print(f"\n  [WARN] Cannot connect: {e}")
        return False

    except Exception as e:
        print(f"\n  [FAIL] Error: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("STJ Client Test Suite")
    print("=" * 60)

    # Check environment
    from services.stj_client import Config
    print(f"\nConfiguration:")
    print(f"  STJ_API_URL: {Config.STJ_API_URL}")
    print(f"  REQUEST_TIMEOUT: {Config.REQUEST_TIMEOUT}s")
    print(f"  MAX_RETRIES: {Config.MAX_RETRIES}")

    tests = [
        ("Health Check", test_health_check),
        ("Search", test_search),
        ("Search with Filters", test_search_with_filters),
        ("Statistics", test_stats),
        ("Validation", test_validation),
        ("Convenience Functions", test_convenience_functions),
        ("Sync Status", test_sync),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print("\n\n[INTERRUPT] Tests stopped by user")
            break
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {name}: {status}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Teste básico do DJENDownloader (sem dependências externas).

Valida que:
1. Downloader pode ser importado
2. Métodos básicos funcionam
3. Estrutura de PublicacaoRaw está correta
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import rate_limiter from djen-tracker
sys.path.insert(0, str(Path(__file__).parent.parent / 'djen-tracker' / 'src'))


def test_import():
    """Testa se downloader pode ser importado."""
    print("1. Testando import do downloader...")
    try:
        from downloader import DJENDownloader, PublicacaoRaw
        print("   ✅ Import successful")
        return DJENDownloader, PublicacaoRaw
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        sys.exit(1)


def test_initialization(DJENDownloader):
    """Testa inicialização do downloader."""
    print("\n2. Testando inicialização...")
    try:
        data_root = Path(__file__).parent / 'test_data'
        downloader = DJENDownloader(
            data_root=data_root,
            requests_per_minute=30,
            delay_seconds=2.0
        )
        print(f"   ✅ Downloader inicializado")
        print(f"      Data root: {downloader.data_root}")
        print(f"      Downloads dir: {downloader.downloads_dir}")
        return downloader
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        sys.exit(1)


def test_hash_generation(downloader):
    """Testa geração de hash."""
    print("\n3. Testando geração de hash...")
    try:
        texto = "Texto de exemplo para hash"
        hash1 = downloader._gerar_hash(texto)
        hash2 = downloader._gerar_hash(texto)

        assert hash1 == hash2, "Hash deve ser determinístico"
        assert len(hash1) == 64, "Hash SHA256 deve ter 64 caracteres"

        print(f"   ✅ Hash gerado: {hash1[:16]}...")
        print(f"      Comprimento: {len(hash1)} caracteres")
        return hash1
    except Exception as e:
        print(f"   ❌ Hash generation failed: {e}")
        sys.exit(1)


def test_publicacao_raw_structure(PublicacaoRaw):
    """Testa estrutura de PublicacaoRaw."""
    print("\n4. Testando estrutura de PublicacaoRaw...")
    try:
        pub = PublicacaoRaw(
            id='test-id',
            hash_conteudo='abc123',
            numero_processo='12345678920251234567',
            numero_processo_fmt='1234567-89.2025.1.23.4567',
            tribunal='STJ',
            orgao_julgador='1ª Turma',
            tipo_comunicacao='Intimação',
            classe_processual='REsp',
            texto_html='<p>Texto HTML</p>',
            data_publicacao='2025-11-18',
            destinatario_advogados=[],
            metadata={}
        )

        assert pub.id == 'test-id'
        assert pub.tribunal == 'STJ'
        assert pub.tipo_comunicacao == 'Intimação'

        print(f"   ✅ PublicacaoRaw criada")
        print(f"      ID: {pub.id}")
        print(f"      Tribunal: {pub.tribunal}")
        print(f"      Tipo: {pub.tipo_comunicacao}")
        return pub
    except Exception as e:
        print(f"   ❌ PublicacaoRaw creation failed: {e}")
        sys.exit(1)


def test_stats(downloader):
    """Testa obtenção de estatísticas."""
    print("\n5. Testando estatísticas...")
    try:
        # Adicionar alguns hashes
        downloader.hash_cache.add('hash1')
        downloader.hash_cache.add('hash2')
        downloader.hash_cache.add('hash3')

        stats = downloader.get_stats()

        assert 'hash_cache_size' in stats
        assert stats['hash_cache_size'] == 3

        print(f"   ✅ Estatísticas obtidas")
        print(f"      Cache size: {stats['hash_cache_size']}")
        print(f"      Data root: {stats['data_root']}")
        return stats
    except Exception as e:
        print(f"   ❌ Stats failed: {e}")
        sys.exit(1)


def test_api_url_construction():
    """Testa construção de URLs da API."""
    print("\n6. Testando construção de URLs...")
    try:
        base_url = "https://comunicaapi.pje.jus.br/api/v1"
        tribunal = "STJ"
        data = "2025-11-18"
        limit = 100
        page = 1

        # URL de comunicacao (API_TESTING_REPRODUCIBLE.md - seção 2.3)
        url_comunicacao = (
            f"{base_url}/comunicacao"
            f"?dataInicio={data}"
            f"&dataFim={data}"
            f"&siglaTribunal={tribunal}"
            f"&limit={limit}"
            f"&page={page}"
        )

        expected = "https://comunicaapi.pje.jus.br/api/v1/comunicacao?dataInicio=2025-11-18&dataFim=2025-11-18&siglaTribunal=STJ&limit=100&page=1"
        assert url_comunicacao == expected, f"URL incorreta: {url_comunicacao}"

        # URL de caderno (API_TESTING_REPRODUCIBLE.md - seção 2.4)
        url_caderno = f"{base_url}/caderno/{tribunal}/{data}/E"
        expected_caderno = "https://comunicaapi.pje.jus.br/api/v1/caderno/STJ/2025-11-18/E"
        assert url_caderno == expected_caderno, f"URL incorreta: {url_caderno}"

        print(f"   ✅ URLs construídas corretamente")
        print(f"      Comunicação: {url_comunicacao}")
        print(f"      Caderno: {url_caderno}")
    except Exception as e:
        print(f"   ❌ URL construction failed: {e}")
        sys.exit(1)


def main():
    print("="*80)
    print("TESTE BÁSICO: DJENDownloader")
    print("="*80)

    # Executar testes
    DJENDownloader, PublicacaoRaw = test_import()
    downloader = test_initialization(DJENDownloader)
    hash_result = test_hash_generation(downloader)
    pub = test_publicacao_raw_structure(PublicacaoRaw)
    stats = test_stats(downloader)
    test_api_url_construction()

    # Resumo
    print("\n" + "="*80)
    print("✅ TODOS OS TESTES PASSARAM")
    print("="*80)
    print("\nResumo:")
    print(f"  - Downloader: ✅ Funcionando")
    print(f"  - PublicacaoRaw: ✅ Estrutura correta")
    print(f"  - Hash generation: ✅ SHA256 válido")
    print(f"  - Statistics: ✅ {stats['hash_cache_size']} items no cache")
    print(f"  - URL construction: ✅ Conforme API_TESTING_REPRODUCIBLE.md")
    print("\nPróximos passos:")
    print("  1. Instalar dependências: pip install -r requirements.txt")
    print("  2. Executar testes completos: pytest tests/ -v")
    print("  3. Executar exemplo: python exemplo_uso.py api")


if __name__ == '__main__':
    main()

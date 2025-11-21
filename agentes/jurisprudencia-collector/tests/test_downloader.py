"""
Testes unitários para DJENDownloader
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.downloader import DJENDownloader, PublicacaoRaw


@pytest.fixture
def temp_data_root(tmp_path):
    """Cria diretório temporário para testes."""
    return tmp_path / 'test_data'


@pytest.fixture
def downloader(temp_data_root):
    """Cria instância de DJENDownloader para testes."""
    return DJENDownloader(
        data_root=temp_data_root,
        requests_per_minute=60,  # Mais rápido para testes
        delay_seconds=0.1,
        max_retries=2
    )


class TestDJENDownloader:
    """Testes para DJENDownloader."""

    def test_init(self, downloader, temp_data_root):
        """Testa inicialização do downloader."""
        assert downloader.data_root == temp_data_root
        assert downloader.downloads_dir.exists()
        assert downloader.logs_dir.exists()
        assert downloader.cache_dir.exists()

    def test_gerar_hash(self, downloader):
        """Testa geração de hash SHA256."""
        texto = "Texto de exemplo para hash"
        hash1 = downloader._gerar_hash(texto)
        hash2 = downloader._gerar_hash(texto)

        # Hash deve ser determinístico
        assert hash1 == hash2

        # Hash deve ser SHA256 válido (64 caracteres hex)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)

        # Hash de texto diferente deve ser diferente
        hash3 = downloader._gerar_hash("Outro texto")
        assert hash1 != hash3

    def test_hash_cache(self, downloader):
        """Testa cache de hashes."""
        # Cache inicial deve estar vazio
        assert len(downloader.hash_cache) == 0

        # Adicionar hash
        hash1 = "abc123"
        downloader.hash_cache.add(hash1)
        assert hash1 in downloader.hash_cache

        # Salvar e recarregar
        downloader._save_hash_cache()
        downloader.hash_cache.clear()
        downloader._load_hash_cache()

        # Hash deve ter sido persistido
        assert hash1 in downloader.hash_cache

    @patch('requests.Session.get')
    def test_baixar_api_success(self, mock_get, downloader):
        """Testa download via API com sucesso."""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'count': 2,
            'items': [
                {
                    'id': 'pub1',
                    'texto': '<p>Publicação 1</p>',
                    'numero_processo': '12345678920251234567',
                    'numeroprocessocommascara': '1234567-89.2025.1.23.4567',
                    'siglaTribunal': 'STJ',
                    'nomeOrgao': '1ª Turma',
                    'tipoComunicacao': 'Intimação',
                    'nomeClasse': 'REsp',
                    'destinatarioadvogados': []
                },
                {
                    'id': 'pub2',
                    'texto': '<p>Publicação 2</p>',
                    'numero_processo': '98765432120251234567',
                    'numeroprocessocommascara': '9876543-21.2025.1.23.4567',
                    'siglaTribunal': 'STJ',
                    'nomeOrgao': '2ª Turma',
                    'tipoComunicacao': 'Intimação',
                    'nomeClasse': 'AgRg',
                    'destinatarioadvogados': []
                }
            ]
        }
        mock_get.return_value = mock_response

        # Executar download
        publicacoes = downloader.baixar_api(
            tribunal='STJ',
            data='2025-11-18',
            limit=100,
            max_pages=1
        )

        # Verificar resultados
        assert len(publicacoes) == 2
        assert all(isinstance(pub, PublicacaoRaw) for pub in publicacoes)

        # Verificar primeira publicação
        pub1 = publicacoes[0]
        assert pub1.id == 'pub1'
        assert pub1.tribunal == 'STJ'
        assert pub1.tipo_comunicacao == 'Intimação'
        assert pub1.numero_processo_fmt == '1234567-89.2025.1.23.4567'
        assert pub1.texto_html == '<p>Publicação 1</p>'

    @patch('requests.Session.get')
    def test_baixar_api_deduplicacao(self, mock_get, downloader):
        """Testa deduplicação de publicações."""
        # Mock com publicação duplicada
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'count': 2,
            'items': [
                {
                    'id': 'pub1',
                    'texto': '<p>Publicação 1</p>',
                    'siglaTribunal': 'STJ',
                    'tipoComunicacao': 'Intimação',
                    'destinatarioadvogados': []
                },
                {
                    'id': 'pub1_dup',  # ID diferente mas texto igual
                    'texto': '<p>Publicação 1</p>',  # Texto duplicado
                    'siglaTribunal': 'STJ',
                    'tipoComunicacao': 'Intimação',
                    'destinatarioadvogados': []
                }
            ]
        }
        mock_get.return_value = mock_response

        # Executar download
        publicacoes = downloader.baixar_api(
            tribunal='STJ',
            data='2025-11-18',
            limit=100,
            max_pages=1
        )

        # Deve retornar apenas 1 publicação (duplicata removida)
        assert len(publicacoes) == 1
        assert publicacoes[0].id == 'pub1'

    @patch('requests.Session.get')
    def test_baixar_caderno_success(self, mock_get, downloader):
        """Testa download de caderno com sucesso."""
        # Mock das respostas (API metadata + S3 ZIP)
        mock_metadata_response = Mock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = {
            'status': 'Processado',
            'comunicacoes': 100,
            'paginas': 10,
            'data_publicacao': '2025-11-18',
            'url': 'https://s3.example.com/caderno.zip'
        }

        mock_zip_response = Mock()
        mock_zip_response.status_code = 200
        mock_zip_response.content = b'fake-zip-content'

        # Configurar mock para retornar respostas diferentes
        mock_get.side_effect = [mock_metadata_response, mock_zip_response]

        # Executar download
        pdf_path, metadata = downloader.baixar_caderno(
            tribunal='STJ',
            data='2025-11-18',
            meio='E'
        )

        # Verificar resultados
        assert pdf_path is not None
        assert pdf_path.exists()
        assert metadata['status'] == 'Processado'
        assert metadata['comunicacoes'] == 100

    @patch('requests.Session.get')
    def test_baixar_api_retry(self, mock_get, downloader):
        """Testa retry automático em caso de falha."""
        # Mock: primeira tentativa falha, segunda sucede
        mock_response_erro = Mock()
        mock_response_erro.status_code = 500
        mock_response_erro.raise_for_status.side_effect = Exception("Server error")

        mock_response_sucesso = Mock()
        mock_response_sucesso.status_code = 200
        mock_response_sucesso.json.return_value = {
            'status': 'success',
            'count': 0,
            'items': []
        }

        mock_get.side_effect = [mock_response_erro, mock_response_sucesso]

        # Executar download (deve ter sucesso após retry)
        publicacoes = downloader.baixar_api(
            tribunal='STJ',
            data='2025-11-18',
            limit=100,
            max_pages=1
        )

        # Deve retornar lista vazia (sem falhar)
        assert publicacoes == []

    def test_salvar_publicacoes(self, downloader):
        """Testa salvamento de publicações em JSON."""
        # Criar publicações de exemplo
        publicacoes = [
            PublicacaoRaw(
                id='pub1',
                hash_conteudo='abc123',
                numero_processo='12345678920251234567',
                numero_processo_fmt='1234567-89.2025.1.23.4567',
                tribunal='STJ',
                orgao_julgador='1ª Turma',
                tipo_comunicacao='Intimação',
                classe_processual='REsp',
                texto_html='<p>Texto 1</p>',
                data_publicacao='2025-11-18',
                destinatario_advogados=[],
                metadata={}
            )
        ]

        # Salvar
        output_path = downloader.salvar_publicacoes(
            publicacoes,
            tribunal='STJ',
            data='2025-11-18'
        )

        # Verificar
        assert output_path is not None
        assert output_path.exists()

        # Verificar conteúdo
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data['tribunal'] == 'STJ'
        assert data['data_publicacao'] == '2025-11-18'
        assert data['total'] == 1
        assert len(data['publicacoes']) == 1
        assert data['publicacoes'][0]['id'] == 'pub1'

    def test_get_stats(self, downloader):
        """Testa obtenção de estatísticas."""
        # Adicionar alguns hashes ao cache
        downloader.hash_cache.add('hash1')
        downloader.hash_cache.add('hash2')

        # Obter estatísticas
        stats = downloader.get_stats()

        # Verificar
        assert 'hash_cache_size' in stats
        assert stats['hash_cache_size'] == 2
        assert 'rate_limiter' in stats
        assert 'data_root' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

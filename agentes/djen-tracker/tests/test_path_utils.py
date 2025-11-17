"""
Testes para módulo path_utils.py - Auto-detecção de ambiente e paths.

Valida:
- Auto-detecção de ambiente (Windows vs WSL2)
- Resolução de data root
- Paths para diretórios de agentes
- Resolução de config paths
- Fallback para home directory
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.path_utils import (
    get_data_root,
    get_agent_data_dir,
    resolve_config_paths,
    detect_environment
)


class TestDetectEnvironment:
    """Testes para detect_environment()."""

    def test_detect_wsl2(self, monkeypatch):
        """Detecta WSL2 quando /mnt/wsl ou /mnt/c existe."""
        # Mock Path.exists() para simular WSL2
        with patch('pathlib.Path.exists') as mock_exists:
            # Primeira chamada: /mnt/wsl existe
            mock_exists.return_value = True

            env = detect_environment()
            assert env == 'wsl2'

    def test_detect_windows(self, monkeypatch):
        """Detecta Windows quando os.name == 'nt'."""
        monkeypatch.setattr('os.name', 'nt')

        with patch('pathlib.Path.exists', return_value=False):
            env = detect_environment()
            assert env == 'windows'

    def test_detect_unknown(self, monkeypatch):
        """Detecta 'unknown' para outros ambientes."""
        monkeypatch.setattr('os.name', 'posix')

        with patch('pathlib.Path.exists', return_value=False):
            env = detect_environment()
            assert env == 'unknown'


class TestGetDataRoot:
    """Testes para get_data_root()."""

    def test_usa_environment_variable_quando_definida(self, monkeypatch, temp_dir):
        """Usa CLAUDE_DATA_ROOT se definida e existe."""
        test_root = temp_dir / "custom_data"
        test_root.mkdir()

        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        data_root = get_data_root()
        assert data_root == test_root

    def test_ignora_env_var_se_nao_existe(self, monkeypatch, temp_dir):
        """Ignora CLAUDE_DATA_ROOT se diretório não existe."""
        fake_path = temp_dir / "nao_existe"
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(fake_path))

        # Deve tentar próximas opções
        data_root = get_data_root()
        assert data_root != fake_path

    def test_usa_wsl_path_quando_existe(self):
        """Usa /mnt/e/claude-code-data se existe."""
        with patch('pathlib.Path.exists') as mock_exists:
            def side_effect(path_obj):
                # Simula que /mnt/e/claude-code-data existe
                return str(path_obj) == '/mnt/e/claude-code-data'

            mock_exists.side_effect = lambda: side_effect(mock_exists.call_args[0])

            # Mock para o Path object
            with patch('pathlib.Path.__new__') as mock_path:
                wsl_path = Path('/mnt/e/claude-code-data')
                mock_path.return_value = wsl_path

                # Mock exists específico para wsl_path
                with patch.object(Path, 'exists', return_value=True):
                    data_root = get_data_root()
                    assert str(data_root) == '/mnt/e/claude-code-data'

    def test_fallback_para_home_directory(self, monkeypatch, temp_dir):
        """Fallback para ~/.claude-code-data se outras opções não existem."""
        # Remove env var
        monkeypatch.delenv('CLAUDE_DATA_ROOT', raising=False)

        # Mock home para temp_dir
        fake_home = temp_dir / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Mock Path.exists para retornar False para WSL e Windows paths
        original_exists = Path.exists

        def mock_exists(self):
            if 'claude-code-data' in str(self) and 'home' in str(self):
                return False  # Será criado
            if '/mnt/e' in str(self) or str(self).startswith('E:'):
                return False
            return original_exists(self)

        with patch.object(Path, 'exists', mock_exists):
            data_root = get_data_root()
            assert '.claude-code-data' in str(data_root)

    def test_cria_fallback_directory_se_nao_existe(self, monkeypatch, temp_dir):
        """Cria ~/.claude-code-data se não existe."""
        monkeypatch.delenv('CLAUDE_DATA_ROOT', raising=False)

        fake_home = temp_dir / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        with patch('pathlib.Path.exists', return_value=False):
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                data_root = get_data_root()

                # Verificar que tentou criar o diretório
                mock_mkdir.assert_called()


class TestGetAgentDataDir:
    """Testes para get_agent_data_dir()."""

    def test_retorna_path_para_agente(self, monkeypatch, temp_dir):
        """Retorna path correto para agente."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        agent_dir = get_agent_data_dir('djen-tracker')

        expected = test_root / 'agentes' / 'djen-tracker'
        assert agent_dir == expected

    def test_retorna_path_com_subdir(self, monkeypatch, temp_dir):
        """Retorna path com subdiretório quando especificado."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        logs_dir = get_agent_data_dir('djen-tracker', 'logs')

        expected = test_root / 'agentes' / 'djen-tracker' / 'logs'
        assert logs_dir == expected

    @pytest.mark.parametrize("agent_name,subdir", [
        ('oab-watcher', 'downloads'),
        ('djen-tracker', 'cache'),
        ('legal-lens', 'outputs'),
    ])
    def test_multiplos_agentes_e_subdirs(self, agent_name, subdir, monkeypatch, temp_dir):
        """Testa múltiplos agentes e subdiretórios."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        agent_dir = get_agent_data_dir(agent_name, subdir)

        expected = test_root / 'agentes' / agent_name / subdir
        assert agent_dir == expected


class TestResolveConfigPaths:
    """Testes para resolve_config_paths()."""

    def test_resolve_data_root_em_config(self, monkeypatch, temp_dir):
        """Resolve data_root em config."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        config = {
            'paths': {
                'data_root': '/old/path',
                'downloads': 'downloads/'
            }
        }

        resolved = resolve_config_paths(config, 'djen-tracker')

        expected_root = str(test_root / 'agentes' / 'djen-tracker')
        assert resolved['paths']['data_root'] == expected_root

    def test_nao_modifica_config_original(self, monkeypatch, temp_dir):
        """Não modifica config original (retorna cópia)."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        original_config = {
            'paths': {
                'data_root': '/old/path'
            }
        }

        original_value = original_config['paths']['data_root']
        resolved = resolve_config_paths(original_config, 'djen-tracker')

        # Original não deve ter mudado
        assert original_config['paths']['data_root'] == original_value

        # Resolved deve ter mudado
        assert resolved['paths']['data_root'] != original_value

    def test_preserva_outros_campos_config(self, monkeypatch, temp_dir):
        """Preserva outros campos de configuração."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        config = {
            'paths': {
                'data_root': '/old/path',
                'custom_field': 'valor'
            },
            'outros': {
                'campo': 123
            }
        }

        resolved = resolve_config_paths(config, 'djen-tracker')

        # Campos não relacionados a data_root devem permanecer
        assert resolved['paths']['custom_field'] == 'valor'
        assert resolved['outros']['campo'] == 123


class TestPathUtilsIntegration:
    """Testes de integração entre funções de path_utils."""

    def test_workflow_completo(self, monkeypatch, temp_dir):
        """Testa workflow completo de detecção e resolução de paths."""
        # Setup
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        # 1. Detectar ambiente
        env = detect_environment()
        assert env in ['wsl2', 'windows', 'unknown']

        # 2. Obter data root
        data_root = get_data_root()
        assert data_root == test_root

        # 3. Obter diretório do agente
        agent_dir = get_agent_data_dir('djen-tracker')
        expected_agent = test_root / 'agentes' / 'djen-tracker'
        assert agent_dir == expected_agent

        # 4. Obter subdiretório
        logs_dir = get_agent_data_dir('djen-tracker', 'logs')
        expected_logs = expected_agent / 'logs'
        assert logs_dir == expected_logs

        # 5. Resolver config
        config = {'paths': {'data_root': '/wrong'}}
        resolved = resolve_config_paths(config, 'djen-tracker')
        assert resolved['paths']['data_root'] == str(expected_agent)

    def test_multiplos_agentes_independentes(self, monkeypatch, temp_dir):
        """Múltiplos agentes têm paths independentes."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        djen_dir = get_agent_data_dir('djen-tracker')
        oab_dir = get_agent_data_dir('oab-watcher')
        lens_dir = get_agent_data_dir('legal-lens')

        # Todos devem ser diferentes
        assert djen_dir != oab_dir
        assert oab_dir != lens_dir
        assert djen_dir != lens_dir

        # Mas compartilham mesmo root
        assert djen_dir.parent.parent == oab_dir.parent.parent
        assert djen_dir.parent.parent == test_root


class TestPathUtilsEdgeCases:
    """Testes de edge cases e situações incomuns."""

    def test_agent_name_vazio(self, monkeypatch, temp_dir):
        """Lida com agent_name vazio."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        agent_dir = get_agent_data_dir('')
        expected = test_root / 'agentes' / ''
        assert agent_dir == expected

    def test_agent_name_com_espacos(self, monkeypatch, temp_dir):
        """Lida com agent_name com espaços."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        agent_dir = get_agent_data_dir('my agent')
        expected = test_root / 'agentes' / 'my agent'
        assert agent_dir == expected

    def test_subdir_com_barras(self, monkeypatch, temp_dir):
        """Lida com subdir contendo barras."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        agent_dir = get_agent_data_dir('djen-tracker', 'logs/2025/11')
        expected = test_root / 'agentes' / 'djen-tracker' / 'logs' / '2025' / '11'
        assert agent_dir == expected

    def test_paths_sao_pathlib(self, monkeypatch, temp_dir):
        """Retorna objetos Path (pathlib), não strings."""
        test_root = temp_dir / "data"
        test_root.mkdir()
        monkeypatch.setenv('CLAUDE_DATA_ROOT', str(test_root))

        data_root = get_data_root()
        assert isinstance(data_root, Path)

        agent_dir = get_agent_data_dir('djen-tracker')
        assert isinstance(agent_dir, Path)

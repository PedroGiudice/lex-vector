import sys
import os
import unittest

# Adiciona o diretório raiz do projeto ao sys.path de forma explícita
# para garantir que o módulo 'adk_agents' seja encontrado.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adk_agents.dpp_agent.agent import root_agent

class TestDppAgent(unittest.TestCase):
    """Test suite for the DPP ADK Agent configuration."""

    def test_agent_initialization_properties(self):
        """
        Verifies that the dpp-agent is initialized with the correct name, model,
        and a non-empty, valid instruction set.
        """
        # 1. Verifica o nome do agente
        self.assertEqual(root_agent.name, "dpp_agent", "Agent name should be 'dpp_agent'")

        # 2. Verifica se o modelo correto está sendo usado
        self.assertEqual(root_agent.model, "gemini-2.5-flash", "Agent model should be 'gemini-2.5-flash'")

        # 3. Verifica se o prompt (instruction) foi carregado e contém texto chave
        self.assertIsInstance(root_agent.instruction, str, "Instruction should be a string")
        self.assertGreater(len(root_agent.instruction), 100, "Instruction should not be a short placeholder")
        self.assertIn("DIRETOR DE PRÉ-PROCESSAMENTO", root_agent.instruction, "Instruction is missing key identity phrase")
        self.assertIn("180-LINE CONTEXT OFFLOADING", root_agent.instruction, "Instruction is missing critical offloading rule")

if __name__ == '__main__':
    unittest.main()

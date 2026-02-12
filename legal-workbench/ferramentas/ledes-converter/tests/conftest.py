"""Configuracao global de testes para o LEDES Converter."""

import os

# Limpa DATA_PATH para evitar conflito com o env de producao/STJ.
# O MatterStore precisa resolver para o diretorio local data/.
os.environ.pop("DATA_PATH", None)

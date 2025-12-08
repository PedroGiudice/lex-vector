# Use uma imagem base oficial do Python
FROM python:3.11-slim

# Instale as dependências do sistema operacional para Tesseract e Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Defina o diretório de trabalho no contêiner
WORKDIR /app

# Copie o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instale as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante dos arquivos da aplicação
COPY . .

# Expõe a porta que o Streamlit usa por padrão
EXPOSE 8501

# Comando para rodar a aplicação
CMD ["streamlit", "run", "app.py"]

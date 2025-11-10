"""
PDF Processor - Extração de texto de PDFs jurídicos
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
import PyPDF2
import pdfplumber
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Chunk de documento com metadata"""
    text: str
    page_number: int
    source_file: str
    metadata: Dict


class PDFProcessor:
    """Processa PDFs jurídicos e extrai texto estruturado"""

    def __init__(self, config: Dict):
        self.config = config
        self.chunk_size = config['rag']['chunk_size']
        self.chunk_overlap = config['rag']['chunk_overlap']

    def extract_text_pypdf2(self, pdf_path: Path) -> str:
        """
        Extrai texto usando PyPDF2 (mais rápido, menos preciso)

        Args:
            pdf_path: Caminho do PDF

        Returns:
            Texto extraído
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Página {page_num} ---\n{page_text}"

            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto com PyPDF2 de {pdf_path}: {e}")
            return ""

    def extract_text_pdfplumber(self, pdf_path: Path) -> List[Dict]:
        """
        Extrai texto usando pdfplumber (mais lento, mais preciso)

        Args:
            pdf_path: Caminho do PDF

        Returns:
            Lista de dicts com texto e metadata por página
        """
        pages_data = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()

                    if text:
                        pages_data.append({
                            'page_number': page_num,
                            'text': text,
                            'width': page.width,
                            'height': page.height,
                            'source': pdf_path.name
                        })

            logger.info(f"Extraídas {len(pages_data)} páginas de {pdf_path.name}")
            return pages_data

        except Exception as e:
            logger.error(f"Erro ao extrair texto com pdfplumber de {pdf_path}: {e}")
            return []

    def extract_metadata(self, pdf_path: Path) -> Dict:
        """
        Extrai metadata do PDF

        Args:
            pdf_path: Caminho do PDF

        Returns:
            Dict com metadata
        """
        metadata = {
            'filename': pdf_path.name,
            'path': str(pdf_path),
            'size_bytes': pdf_path.stat().st_size,
            'num_pages': 0,
            'tribunal': self._extract_tribunal_from_filename(pdf_path.name),
            'data': self._extract_date_from_filename(pdf_path.name)
        }

        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata['num_pages'] = len(reader.pages)

                # Metadata do PDF
                if reader.metadata:
                    metadata['pdf_title'] = reader.metadata.get('/Title', '')
                    metadata['pdf_author'] = reader.metadata.get('/Author', '')
                    metadata['pdf_subject'] = reader.metadata.get('/Subject', '')
                    metadata['pdf_creator'] = reader.metadata.get('/Creator', '')

        except Exception as e:
            logger.warning(f"Erro ao extrair metadata de {pdf_path}: {e}")

        return metadata

    def _extract_tribunal_from_filename(self, filename: str) -> Optional[str]:
        """Tenta extrair tribunal do nome do arquivo"""
        # Padrão comum: TJSP_2025-01-15_caderno.pdf
        match = re.search(r'(TJ[A-Z]{2}|TRF\d|STJ|STF|TST)', filename, re.IGNORECASE)
        return match.group(1).upper() if match else None

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Tenta extrair data do nome do arquivo"""
        # Padrão: YYYY-MM-DD
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        return match.group(1) if match else None

    def chunk_text(self, text: str, metadata: Dict) -> List[DocumentChunk]:
        """
        Divide texto em chunks com overlap

        Args:
            text: Texto completo
            metadata: Metadata do documento

        Returns:
            Lista de chunks
        """
        chunks = []

        # Dividir por parágrafos primeiro
        paragraphs = text.split('\n\n')

        current_chunk = ""
        current_size = 0
        chunk_number = 0

        for para in paragraphs:
            para_size = len(para)

            # Se parágrafo cabe no chunk atual
            if current_size + para_size <= self.chunk_size:
                current_chunk += para + "\n\n"
                current_size += para_size
            else:
                # Salvar chunk atual
                if current_chunk:
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        page_number=metadata.get('page_number', 0),
                        source_file=metadata['filename'],
                        metadata={
                            **metadata,
                            'chunk_number': chunk_number,
                            'chunk_size': len(current_chunk)
                        }
                    ))
                    chunk_number += 1

                # Iniciar novo chunk (com overlap se configurado)
                if self.chunk_overlap > 0 and current_chunk:
                    # Pegar últimas palavras do chunk anterior
                    words = current_chunk.split()
                    overlap_words = words[-self.chunk_overlap:]
                    current_chunk = ' '.join(overlap_words) + "\n\n" + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"

                current_size = len(current_chunk)

        # Adicionar último chunk
        if current_chunk:
            chunks.append(DocumentChunk(
                text=current_chunk.strip(),
                page_number=metadata.get('page_number', 0),
                source_file=metadata['filename'],
                metadata={
                    **metadata,
                    'chunk_number': chunk_number,
                    'chunk_size': len(current_chunk)
                }
            ))

        logger.info(f"Texto dividido em {len(chunks)} chunks")
        return chunks

    def process_pdf(self, pdf_path: Path, method: str = 'pdfplumber') -> List[DocumentChunk]:
        """
        Processa PDF completo e retorna chunks

        Args:
            pdf_path: Caminho do PDF
            method: 'pypdf2' ou 'pdfplumber'

        Returns:
            Lista de chunks processados
        """
        logger.info(f"Processando PDF: {pdf_path.name}")

        # Extrair metadata
        metadata = self.extract_metadata(pdf_path)

        all_chunks = []

        if method == 'pdfplumber':
            pages_data = self.extract_text_pdfplumber(pdf_path)

            for page_data in pages_data:
                page_metadata = {**metadata, **page_data}
                chunks = self.chunk_text(page_data['text'], page_metadata)
                all_chunks.extend(chunks)

        else:  # pypdf2
            text = self.extract_text_pypdf2(pdf_path)
            if text:
                chunks = self.chunk_text(text, metadata)
                all_chunks.extend(chunks)

        logger.info(f"PDF processado: {len(all_chunks)} chunks gerados")
        return all_chunks

    def batch_process_pdfs(self, pdf_paths: List[Path], method: str = 'pdfplumber') -> List[DocumentChunk]:
        """
        Processa múltiplos PDFs em batch

        Args:
            pdf_paths: Lista de caminhos de PDFs
            method: Método de extração

        Returns:
            Lista consolidada de chunks
        """
        all_chunks = []

        logger.info(f"Processando batch de {len(pdf_paths)} PDFs")

        for pdf_path in pdf_paths:
            try:
                chunks = self.process_pdf(pdf_path, method)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Erro ao processar {pdf_path}: {e}")

        logger.info(f"Batch processado: {len(all_chunks)} chunks totais de {len(pdf_paths)} PDFs")
        return all_chunks

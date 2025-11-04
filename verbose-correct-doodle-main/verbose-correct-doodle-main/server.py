#!/usr/bin/env python3
"""
MD2PDF Converter - Servidor HTTP Local
Servidor web simples multiplataforma
"""

import http.server
import socketserver
import os
import sys
from datetime import datetime

PORT = 8000
DIRECTORY = "."

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        """Log personalizado com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"[{timestamp}] {args[0]} {args[1]}\n")
        sys.stdout.flush()

    def end_headers(self):
        """Adiciona headers CORS e cache"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def guess_type(self, path):
        """Melhora detecção de MIME types"""
        mime_type = super().guess_type(path)

        # Correções para tipos específicos
        if path.endswith('.js'):
            return 'application/javascript; charset=utf-8'
        elif path.endswith('.mjs'):
            return 'application/javascript; charset=utf-8'
        elif path.endswith('.css'):
            return 'text/css; charset=utf-8'
        elif path.endswith('.json'):
            return 'application/json; charset=utf-8'
        elif path.endswith('.woff'):
            return 'font/woff'
        elif path.endswith('.woff2'):
            return 'font/woff2'
        elif path.endswith('.ttf'):
            return 'font/ttf'
        elif path.endswith('.eot'):
            return 'application/vnd.ms-fontobject'

        return mime_type

def main():
    """Inicia o servidor HTTP"""
    print("=" * 40)
    print("  MD2PDF CONVERTER - SERVER")
    print("=" * 40)
    print()
    print(f"Servidor iniciando...")
    print(f"Porta: {PORT}")
    print(f"Diretório: {os.path.abspath(DIRECTORY)}")
    print()
    print(f"Acesse: http://localhost:{PORT}")
    print("Pressione Ctrl+C para encerrar")
    print()

    # Desabilita buffer de saída para logs em tempo real
    sys.stdout.reconfigure(line_buffering=True)

    # Cria servidor TCP reutilizável
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            print(f"[OK] Servidor rodando em http://localhost:{PORT}")
            print()

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print()
                print("[INFO] Servidor encerrado")
                sys.exit(0)

    except OSError as e:
        if e.errno == 98 or e.errno == 10048:  # Address already in use
            print(f"[ERRO] Porta {PORT} já está em uso")
            print(f"       Tente outro número de porta ou encerre o processo que está usando a porta {PORT}")
            sys.exit(1)
        else:
            print(f"[ERRO] Erro ao iniciar servidor: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

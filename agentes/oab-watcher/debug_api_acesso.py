"""
Debug API Access - Testar diferentes formas de acessar a API DJEN
"""
import requests
from datetime import datetime, timedelta

BASE_URL = "https://comunicaapi.pje.jus.br"
PORTAL_URL = "https://comunica.pje.jus.br"

def test_1_basic_request():
    """Teste 1: Requisição básica sem headers especiais"""
    print("\n" + "="*80)
    print("TESTE 1: Requisição Básica")
    print("="*80)

    url = f"{BASE_URL}/api/v1/comunicacao"
    params = {
        'data_inicio': '2025-11-06',
        'data_fim': '2025-11-06'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
        return resp
    except Exception as e:
        print(f"Erro: {e}")
        return None


def test_2_browser_headers():
    """Teste 2: Simular navegador com headers completos"""
    print("\n" + "="*80)
    print("TESTE 2: Simulando Navegador")
    print("="*80)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://comunica.pje.jus.br/',
        'Origin': 'https://comunica.pje.jus.br',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

    url = f"{BASE_URL}/api/v1/comunicacao"
    params = {
        'data_inicio': '2025-11-06',
        'data_fim': '2025-11-06'
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Headers retornados: {dict(resp.headers)}")
        print(f"Response: {resp.text[:200]}")
        return resp
    except Exception as e:
        print(f"Erro: {e}")
        return None


def test_3_session_with_cookies():
    """Teste 3: Usar sessão com cookies"""
    print("\n" + "="*80)
    print("TESTE 3: Usando Session com Cookies")
    print("="*80)

    session = requests.Session()

    # Headers de navegador
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'pt-BR,pt;q=0.9',
    })

    # Primeiro, acessar o portal para pegar cookies
    print("\nPasso 1: Acessando portal para pegar cookies...")
    try:
        portal_resp = session.get(PORTAL_URL, timeout=10)
        print(f"  Portal Status: {portal_resp.status_code}")
        print(f"  Cookies obtidos: {session.cookies.get_dict()}")
    except Exception as e:
        print(f"  Erro ao acessar portal: {e}")

    # Depois, tentar API com os cookies
    print("\nPasso 2: Tentando API com cookies...")
    url = f"{BASE_URL}/api/v1/comunicacao"
    params = {
        'data_inicio': '2025-11-06',
        'data_fim': '2025-11-06'
    }

    try:
        resp = session.get(url, params=params, timeout=10)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:200]}")
        return resp
    except Exception as e:
        print(f"  Erro: {e}")
        return None


def test_4_different_endpoints():
    """Teste 4: Testar diferentes endpoints"""
    print("\n" + "="*80)
    print("TESTE 4: Testando Diferentes Endpoints")
    print("="*80)

    endpoints = [
        '/api/v1/comunicacao',
        '/api/v1/cadernos',
        '/api/v1/public/comunicacao',
        '/api/comunicacao',
        '/comunicacao',
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    params = {
        'data': '2025-11-06'
    }

    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"\nTestando: {url}")

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            print(f"  ✓ Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  Response preview: {resp.text[:100]}")
        except Exception as e:
            print(f"  ✗ Erro: {e}")


def test_5_check_ssl_certificates():
    """Teste 5: Verificar problemas com SSL"""
    print("\n" + "="*80)
    print("TESTE 5: Testando com/sem verificação SSL")
    print("="*80)

    url = f"{BASE_URL}/api/v1/comunicacao"
    params = {
        'data_inicio': '2025-11-06',
        'data_fim': '2025-11-06'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    # Com verificação SSL
    print("\nCom verificação SSL (verify=True):")
    try:
        resp = requests.get(url, params=params, headers=headers, verify=True, timeout=10)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:200]}")
    except Exception as e:
        print(f"  Erro: {e}")

    # Sem verificação SSL
    print("\nSem verificação SSL (verify=False):")
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        resp = requests.get(url, params=params, headers=headers, verify=False, timeout=10)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:200]}")
        return resp
    except Exception as e:
        print(f"  Erro: {e}")
        return None


def test_6_with_auth_token():
    """Teste 6: Verificar se precisa de token de autenticação"""
    print("\n" + "="*80)
    print("TESTE 6: Testando com Token de Autenticação")
    print("="*80)

    url = f"{BASE_URL}/api/v1/comunicacao"
    params = {
        'data_inicio': '2025-11-06',
        'data_fim': '2025-11-06'
    }

    # Tentar diferentes formatos de autenticação
    auth_headers_variants = [
        {'Authorization': 'Bearer TOKEN_TESTE'},
        {'X-API-Key': 'API_KEY_TESTE'},
        {'Token': 'TOKEN_TESTE'},
    ]

    for auth_headers in auth_headers_variants:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            **auth_headers
        }

        print(f"\nTestando com: {list(auth_headers.keys())[0]}")
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {resp.text[:100]}")
        except Exception as e:
            print(f"  Erro: {e}")


def test_7_check_robots_txt():
    """Teste 7: Verificar robots.txt e política de acesso"""
    print("\n" + "="*80)
    print("TESTE 7: Verificando robots.txt")
    print("="*80)

    urls_to_check = [
        f"{BASE_URL}/robots.txt",
        f"{BASE_URL}/.well-known/security.txt",
        f"{PORTAL_URL}/robots.txt",
    ]

    for url in urls_to_check:
        print(f"\nTestando: {url}")
        try:
            resp = requests.get(url, timeout=5)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  Conteúdo:\n{resp.text[:500]}")
        except Exception as e:
            print(f"  Erro: {e}")


def test_8_cors_preflight():
    """Teste 8: Testar OPTIONS request (CORS preflight)"""
    print("\n" + "="*80)
    print("TESTE 8: Testando CORS Preflight (OPTIONS)")
    print("="*80)

    url = f"{BASE_URL}/api/v1/comunicacao"

    headers = {
        'Origin': 'https://comunica.pje.jus.br',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'content-type',
    }

    try:
        resp = requests.options(url, headers=headers, timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Headers retornados:")
        for key, value in resp.headers.items():
            if 'access-control' in key.lower() or 'cors' in key.lower():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Erro: {e}")


def main():
    """Executar todos os testes de debug"""
    print("\n" + "#"*80)
    print("DEBUG DE ACESSO - API DJEN")
    print("#"*80)
    print(f"Timestamp: {datetime.now()}")
    print(f"Base URL: {BASE_URL}")

    # Executar testes em sequência
    tests = [
        test_1_basic_request,
        test_2_browser_headers,
        test_3_session_with_cookies,
        test_4_different_endpoints,
        test_5_check_ssl_certificates,
        test_6_with_auth_token,
        test_7_check_robots_txt,
        test_8_cors_preflight,
    ]

    results = {}
    for test_func in tests:
        try:
            result = test_func()
            results[test_func.__name__] = result
        except Exception as e:
            print(f"\n✗ Erro ao executar {test_func.__name__}: {e}")
            results[test_func.__name__] = None

    # Resumo
    print("\n" + "#"*80)
    print("RESUMO DOS TESTES")
    print("#"*80)

    for test_name, result in results.items():
        if result and hasattr(result, 'status_code'):
            status = f"Status {result.status_code}"
            if result.status_code == 200:
                print(f"✓ {test_name}: {status} - SUCESSO!")
            elif result.status_code == 403:
                print(f"✗ {test_name}: {status} - Access Denied")
            else:
                print(f"⚠ {test_name}: {status}")
        else:
            print(f"✗ {test_name}: Falhou ou sem response")

    print("\n" + "#"*80)


if __name__ == "__main__":
    main()

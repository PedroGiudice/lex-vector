# MD2PDF Converter - Servidor HTTP Local
# Servidor web simples para desenvolvimento

param(
    [int]$Port = 8000,
    [string]$Directory = "."
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MD2PDF CONVERTER - SERVER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servidor iniciando..." -ForegroundColor Green
Write-Host "Porta: $Port" -ForegroundColor Gray
Write-Host "Diretório: $(Resolve-Path $Directory)" -ForegroundColor Gray
Write-Host ""
Write-Host "Acesse: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para encerrar" -ForegroundColor Yellow
Write-Host ""

# Cria listener HTTP
$http = [System.Net.HttpListener]::new()
$http.Prefixes.Add("http://localhost:$Port/")

try {
    $http.Start()
} catch {
    Write-Host "[ERRO] Não foi possível iniciar o servidor" -ForegroundColor Red
    Write-Host "       Verifique se a porta $Port está disponível" -ForegroundColor Red
    exit 1
}

if (-not $http.IsListening) {
    Write-Host "[ERRO] Não foi possível iniciar o servidor" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Servidor rodando em http://localhost:$Port" -ForegroundColor Green
Write-Host ""

# Loop principal
try {
    while ($http.IsListening) {
        $context = $http.GetContext()
        $request = $context.Request
        $response = $context.Response

        # Loga requisição
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] $($request.HttpMethod) $($request.Url.LocalPath)" -ForegroundColor Gray

        # Determina arquivo
        $filename = $request.Url.LocalPath
        if ($filename -eq '/') {
            $filename = '/index.html'
        }

        $filepath = Join-Path $Directory $filename.TrimStart('/')

        # Verifica se arquivo existe
        if (Test-Path $filepath -PathType Leaf) {
            # Determina Content-Type
            $ext = [System.IO.Path]::GetExtension($filepath)
            $contentType = switch ($ext) {
                '.html' { 'text/html; charset=utf-8' }
                '.css'  { 'text/css; charset=utf-8' }
                '.js'   { 'application/javascript; charset=utf-8' }
                '.json' { 'application/json; charset=utf-8' }
                '.png'  { 'image/png' }
                '.jpg'  { 'image/jpeg' }
                '.jpeg' { 'image/jpeg' }
                '.gif'  { 'image/gif' }
                '.svg'  { 'image/svg+xml' }
                '.ico'  { 'image/x-icon' }
                '.woff' { 'font/woff' }
                '.woff2' { 'font/woff2' }
                '.ttf'  { 'font/ttf' }
                '.eot'  { 'application/vnd.ms-fontobject' }
                default { 'application/octet-stream' }
            }

            # Lê arquivo
            $content = [System.IO.File]::ReadAllBytes($filepath)

            # Envia resposta
            $response.ContentType = $contentType
            $response.ContentLength64 = $content.Length
            $response.StatusCode = 200

            # Headers CORS (opcional)
            $response.Headers.Add("Access-Control-Allow-Origin", "*")
            $response.Headers.Add("Cache-Control", "no-cache")

            $response.OutputStream.Write($content, 0, $content.Length)
        } else {
            # 404 Not Found
            $response.StatusCode = 404
            $response.ContentType = "text/html; charset=utf-8"
            $message = [System.Text.Encoding]::UTF8.GetBytes(@"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>404 - Not Found</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 50px; }
        h1 { color: #999; }
    </style>
</head>
<body>
    <h1>404</h1>
    <p>Arquivo não encontrado: $($request.Url.LocalPath)</p>
</body>
</html>
"@)
            $response.OutputStream.Write($message, 0, $message.Length)
        }

        $response.Close()
    }
} catch {
    Write-Host ""
    Write-Host "[ERRO] Erro durante execução: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    $http.Stop()
    Write-Host ""
    Write-Host "[INFO] Servidor encerrado" -ForegroundColor Yellow
}

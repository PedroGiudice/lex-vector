<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ $title ?? 'LEDES Converter' }}</title>
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="min-h-screen bg-gray-50 text-gray-900 antialiased">
    <header class="border-b border-gray-200 bg-white">
        <div class="mx-auto max-w-5xl px-4 py-4">
            <h1 class="text-lg font-semibold tracking-tight">LEDES Converter</h1>
            <p class="text-sm text-gray-500">Gerador de faturas LEDES 1998B</p>
        </div>
    </header>

    <main class="mx-auto max-w-5xl px-4 py-8">
        {{ $slot }}
    </main>

    <footer class="mt-auto border-t border-gray-200 bg-white">
        <div class="mx-auto max-w-5xl px-4 py-3">
            <p class="text-xs text-gray-400">LEDES 1998B | Ferramenta interna</p>
        </div>
    </footer>
</body>
</html>

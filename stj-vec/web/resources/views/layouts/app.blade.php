<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'STJ-Vec')</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-900 min-h-screen">
    <header class="bg-white border-b border-gray-200 px-6 py-4">
        <h1 class="text-xl font-semibold">
            <a href="{{ route('search.index') }}">STJ-Vec</a>
            <span class="text-sm font-normal text-gray-500 ml-2">Busca Vetorial de Jurisprudencia</span>
        </h1>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-8">
        @yield('content')
    </main>
</body>
</html>

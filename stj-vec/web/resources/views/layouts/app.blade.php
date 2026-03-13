<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'STJ-Vec')</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        navy: {
                            50: '#f0f4f8',
                            100: '#d9e2ec',
                            200: '#bcccdc',
                            300: '#9fb3c8',
                            400: '#829ab1',
                            500: '#627d98',
                            600: '#486581',
                            700: '#334e68',
                            800: '#243b53',
                            900: '#1B365D',
                        }
                    }
                }
            }
        }
    </script>
    @livewireStyles
</head>
<body class="bg-gray-50 text-gray-800 min-h-screen">
    <header class="bg-navy-900 text-white px-6 py-4 shadow-md">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <h1 class="text-xl font-semibold tracking-tight">
                <a href="{{ route('search.index') }}" class="hover:text-navy-200 transition-colors">STJ-Vec</a>
                <span class="text-sm font-normal text-navy-300 ml-2">Busca Vetorial de Jurisprudencia</span>
            </h1>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-6">
        @yield('content')
    </main>

    @livewireScripts
</body>
</html>

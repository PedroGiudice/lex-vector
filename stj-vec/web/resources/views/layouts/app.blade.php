<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'STJ-Vec')</title>
    <style>{!! App\Services\Theme\ThemeService::cssVariables() !!}</style>
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600&family=jetbrains-mono:400,500&display=swap" rel="stylesheet" />
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @livewireStyles
</head>
<body class="min-h-screen bg-[var(--c-surface-page)] text-[var(--c-text)] antialiased">
    <header class="bg-[var(--c-surface-header)] px-6 py-3.5">
        <div class="flex items-center justify-between">
            <h1 class="text-xl font-semibold tracking-tight">
                <a href="{{ route('search.index') }}" class="text-[var(--c-text-on-header)] hover:opacity-80 transition-opacity">STJ-Vec</a>
                <span class="text-sm font-normal text-[var(--c-text-on-header-muted)] ml-2">Busca Vetorial de Jurisprudencia</span>
            </h1>
            <div class="flex items-center gap-4">
                <span class="text-xs text-[var(--c-text-on-header-muted)]">{{ auth()->user()->name }}</span>
                <a href="{{ route('settings.themes') }}" class="text-[var(--c-text-on-header-muted)] hover:text-[var(--c-text-on-header)] transition-colors" title="Temas">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                </a>
                <form method="POST" action="{{ route('logout') }}" class="inline">
                    @csrf
                    <button type="submit" class="text-xs text-[var(--c-text-on-header-muted)] hover:text-[var(--c-text-on-header)] transition-colors">Sair</button>
                </form>
            </div>
        </div>
    </header>

    <div class="flex min-h-[calc(100vh-52px)]">
        {{-- Sidebar --}}
        <aside class="w-60 flex-shrink-0 bg-[var(--c-surface-sidebar)] border-r border-[var(--c-border)] hidden lg:block">
            <livewire:search-history />
        </aside>

        {{-- Main content --}}
        <main class="flex-1 min-w-0 px-6 py-6">
            <div class="max-w-7xl mx-auto">
                @yield('content')
            </div>
        </main>
    </div>

    @livewireScripts
</body>
</html>

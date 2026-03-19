<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - STJ-Vec</title>
    <style>{!! App\Services\Theme\ThemeService::cssVariables() !!}</style>
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600&display=swap" rel="stylesheet" />
    @vite(['resources/css/app.css'])
</head>
<body class="min-h-screen bg-[var(--c-surface-page)] flex items-center justify-center antialiased">
    <div class="w-full max-w-sm px-6">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-semibold text-[var(--c-text)] tracking-tight">STJ-Vec</h1>
            <p class="text-sm text-[var(--c-text-muted)] mt-1">Busca Vetorial de Jurisprudencia</p>
        </div>

        <div class="bg-[var(--c-surface-card)] rounded-lg border border-[var(--c-border)] p-6">
            @if ($errors->any())
                <div class="mb-4 text-sm text-[var(--c-accent-danger)] bg-red-50 rounded-md px-3 py-2">
                    {{ $errors->first() }}
                </div>
            @endif

            <form method="POST" action="{{ route('login') }}">
                @csrf

                <div class="mb-4">
                    <label for="name" class="block text-xs font-medium text-[var(--c-text-secondary)] mb-1.5">Usuario</label>
                    <input
                        type="text"
                        id="name"
                        name="name"
                        value="{{ old('name') }}"
                        class="w-full px-3 py-2 border border-[var(--c-border)] rounded-md text-sm text-[var(--c-text)] bg-[var(--c-surface-card)] focus:outline-none focus:ring-2 focus:ring-[var(--c-accent)]/40 focus:border-[var(--c-accent)] transition-colors"
                        placeholder="PGR, ABP ou BBT"
                        required
                        autofocus
                    >
                </div>

                <div class="mb-5">
                    <label for="password" class="block text-xs font-medium text-[var(--c-text-secondary)] mb-1.5">Senha</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        class="w-full px-3 py-2 border border-[var(--c-border)] rounded-md text-sm text-[var(--c-text)] bg-[var(--c-surface-card)] focus:outline-none focus:ring-2 focus:ring-[var(--c-accent)]/40 focus:border-[var(--c-accent)] transition-colors"
                        required
                    >
                </div>

                <div class="flex items-center justify-between mb-5">
                    <label class="inline-flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" name="remember" class="rounded border-[var(--c-border)] text-[var(--c-accent)] focus:ring-[var(--c-accent)]">
                        <span class="text-xs text-[var(--c-text-muted)]">Lembrar</span>
                    </label>
                </div>

                <button
                    type="submit"
                    class="w-full px-4 py-2.5 bg-[var(--c-btn-primary)] text-[var(--c-btn-primary-text)] rounded-md hover:bg-[var(--c-btn-primary-hover)] transition-colors text-sm font-medium"
                >
                    Entrar
                </button>
            </form>
        </div>
    </div>
</body>
</html>

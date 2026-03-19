<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Criar Senha - STJ-Vec</title>
    <style>{!! App\Services\Theme\ThemeService::cssVariables() !!}</style>
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=inter:400,500,600&display=swap" rel="stylesheet" />
    @vite(['resources/css/app.css'])
</head>
<body class="min-h-screen bg-[var(--c-surface-page)] flex items-center justify-center antialiased">
    <div class="w-full max-w-sm px-6">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-semibold text-[var(--c-text)] tracking-tight">STJ-Vec</h1>
            <p class="text-sm text-[var(--c-text-muted)] mt-1">Crie sua senha de acesso</p>
        </div>

        <div class="bg-[var(--c-surface-card)] rounded-lg border border-[var(--c-border)] p-6">
            <p class="text-sm text-[var(--c-text-secondary)] mb-4">
                Bem-vindo, <strong>{{ auth()->user()->name }}</strong>. Defina uma senha para continuar.
            </p>

            @if ($errors->any())
                <div class="mb-4 text-sm text-[var(--c-accent-danger)] bg-red-50 rounded-md px-3 py-2">
                    @foreach ($errors->all() as $error)
                        <p>{{ $error }}</p>
                    @endforeach
                </div>
            @endif

            <form method="POST" action="{{ route('auth.password.update') }}">
                @csrf

                <div class="mb-4">
                    <label for="password" class="block text-xs font-medium text-[var(--c-text-secondary)] mb-1.5">Nova senha</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        class="w-full px-3 py-2 border border-[var(--c-border)] rounded-md text-sm text-[var(--c-text)] bg-[var(--c-input-bg)] focus:outline-none focus:ring-2 focus:ring-[var(--c-input-focus)]/40 focus:border-[var(--c-input-focus)] transition-colors"
                        required
                        autofocus
                        minlength="8"
                    >
                    <p class="text-[10px] text-[var(--c-text-muted)] mt-1">Minimo 8 caracteres</p>
                </div>

                <div class="mb-5">
                    <label for="password_confirmation" class="block text-xs font-medium text-[var(--c-text-secondary)] mb-1.5">Confirmar senha</label>
                    <input
                        type="password"
                        id="password_confirmation"
                        name="password_confirmation"
                        class="w-full px-3 py-2 border border-[var(--c-border)] rounded-md text-sm text-[var(--c-text)] bg-[var(--c-input-bg)] focus:outline-none focus:ring-2 focus:ring-[var(--c-input-focus)]/40 focus:border-[var(--c-input-focus)] transition-colors"
                        required
                        minlength="8"
                    >
                </div>

                <button
                    type="submit"
                    class="w-full px-4 py-2.5 bg-[var(--c-btn-primary)] text-[var(--c-btn-primary-text)] rounded-md hover:bg-[var(--c-btn-primary-hover)] transition-colors text-sm font-medium"
                >
                    Definir Senha
                </button>
            </form>
        </div>
    </div>
</body>
</html>

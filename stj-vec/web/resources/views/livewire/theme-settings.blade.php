<div class="flex gap-6">
    {{-- Theme list --}}
    <div class="w-56 shrink-0 space-y-2">
        <h3 class="text-xs font-semibold text-[var(--c-text-muted)] uppercase tracking-wider px-1">Temas</h3>

        <div class="space-y-0.5">
            @foreach ($this->themes as $theme)
                <button
                    wire:click="selectTheme({{ $theme->id }})"
                    wire:key="theme-{{ $theme->id }}"
                    class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                        {{ $selectedThemeId === $theme->id ? 'bg-[var(--c-surface-raised)] text-[var(--c-text)]' : 'text-[var(--c-text-secondary)] hover:bg-[var(--c-surface-raised)]/50' }}"
                >
                    <div class="flex items-center justify-between">
                        <span class="truncate">{{ $theme->name }}</span>
                        @if ($theme->is_active)
                            <span class="w-2 h-2 rounded-full bg-[var(--c-accent-success)] shrink-0 ml-2"></span>
                        @endif
                    </div>
                </button>
            @endforeach
        </div>

        <button
            wire:click="newTheme"
            class="w-full px-3 py-2 text-sm font-medium text-[var(--c-btn-primary-text)] bg-[var(--c-btn-primary)] rounded-md hover:bg-[var(--c-btn-primary-hover)] transition-colors mt-3"
        >
            Novo Tema
        </button>
    </div>

    {{-- Editor --}}
    <div class="flex-1 min-w-0">
        @if ($selectedThemeId)
            <div class="space-y-4">
                {{-- Name + actions --}}
                <div class="flex items-center gap-3">
                    <input
                        type="text"
                        wire:model="themeName"
                        class="bg-[var(--c-surface-card)] border border-[var(--c-border)] rounded-md px-3 py-1.5 text-sm text-[var(--c-text)] focus:outline-none focus:ring-2 focus:ring-[var(--c-accent)] w-48"
                        placeholder="Nome do tema"
                    >
                    <div class="flex items-center gap-2 ml-auto">
                        <button wire:click="save" class="px-3 py-1.5 text-sm font-medium text-[var(--c-btn-primary-text)] bg-[var(--c-btn-primary)] rounded-md hover:bg-[var(--c-btn-primary-hover)] transition-colors">
                            Salvar
                        </button>
                        <button wire:click="activate" class="px-3 py-1.5 text-sm text-[var(--c-accent-success)] border border-[var(--c-border)] rounded-md hover:bg-[var(--c-surface-raised)] transition-colors">
                            Ativar
                        </button>
                        <button wire:click="resetToDefaults" class="px-3 py-1.5 text-sm text-[var(--c-text-muted)] border border-[var(--c-border)] rounded-md hover:bg-[var(--c-surface-raised)] transition-colors">
                            Reset
                        </button>
                        <button wire:click="deleteTheme" wire:confirm="Deletar este tema?" class="px-3 py-1.5 text-sm text-[var(--c-accent-danger)] border border-[var(--c-border)] rounded-md hover:bg-red-50 transition-colors">
                            Deletar
                        </button>
                    </div>
                </div>

                {{-- Status --}}
                @if ($statusMessage)
                    <div class="text-sm px-3 py-2 rounded-md
                        {{ $statusType === 'error' ? 'bg-red-50 text-[var(--c-accent-danger)]' : '' }}
                        {{ $statusType === 'success' ? 'bg-green-50 text-[var(--c-accent-success)]' : '' }}
                        {{ $statusType === 'info' ? 'bg-blue-50 text-blue-700' : '' }}
                    ">
                        {{ $statusMessage }}
                    </div>
                @endif

                {{-- TOML editor --}}
                <textarea
                    wire:model="editorContent"
                    rows="24"
                    spellcheck="false"
                    class="w-full bg-[var(--c-surface-card)] border border-[var(--c-border)] rounded-lg px-4 py-3 text-xs font-mono text-[var(--c-text)] placeholder-[var(--c-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--c-accent)] resize-y leading-relaxed"
                    placeholder="[surface]&#10;page = &quot;#f8f9fb&quot;&#10;..."
                ></textarea>
            </div>
        @else
            <div class="flex items-center justify-center py-16">
                <p class="text-[var(--c-text-muted)] text-sm">Selecione um tema ou crie um novo.</p>
            </div>
        @endif
    </div>
</div>

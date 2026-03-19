<div>
    {{-- Driver selector --}}
    <div class="mb-3 flex items-center gap-3">
        <span class="text-xs text-[var(--c-text-muted)] font-medium">Motor:</span>
        <label class="inline-flex items-center gap-1.5 cursor-pointer">
            <input type="radio" wire:model="driver" value="cli" class="accent-[var(--c-accent)]" @if($status === 'searching') disabled @endif>
            <span class="text-xs text-[var(--c-text-secondary)]">CLI (claude agent)</span>
        </label>
        <label class="inline-flex items-center gap-1.5 cursor-pointer">
            <input type="radio" wire:model="driver" value="sdk" class="accent-[var(--c-accent)]" @if($status === 'searching') disabled @endif>
            <span class="text-xs text-[var(--c-text-secondary)]">SDK (bun + anthropic)</span>
        </label>
    </div>

    {{-- Search Form --}}
    <form wire:submit="startSearch" class="mb-6">
        <div class="flex gap-2">
            <input
                type="text"
                wire:model="query"
                placeholder="Ex: dano moral negativacao indevida banco"
                class="flex-1 px-4 py-2.5 border border-[var(--c-border)] rounded-lg focus:ring-2 focus:ring-[var(--c-input-focus)]/40 focus:border-[var(--c-accent)] text-[var(--c-text)] placeholder-[var(--c-text-muted)] bg-[var(--c-surface-card)] transition-colors"
                @if($status === 'searching') disabled @endif
                minlength="3"
                maxlength="500"
                required
            >
            @if($status === 'searching')
                <button
                    type="button"
                    wire:click="cancelSearch"
                    class="px-6 py-2.5 bg-[var(--c-accent-danger)] text-white rounded-lg hover:opacity-90 transition-opacity font-medium text-sm"
                >
                    Cancelar
                </button>
            @else
                <button
                    type="submit"
                    class="px-6 py-2.5 bg-[var(--c-btn-primary)] text-[var(--c-btn-primary-text)] rounded-lg hover:bg-[var(--c-btn-primary-hover)] transition-colors font-medium text-sm"
                >
                    Decompor e Buscar
                </button>
            @endif
        </div>
        @error('query')
            <p class="mt-2 text-sm text-[var(--c-accent-danger)]">{{ $message }}</p>
        @enderror
    </form>

    {{-- Searching State --}}
    @if($status === 'searching')
        <div x-data="{
                seconds: 0,
                timerInterval: null,
                es: null,
                angles: [],
                currentAngle: null,
                init() {
                    this.timerInterval = setInterval(() => {
                        this.seconds++;
                        if (this.seconds > 600) {
                            this.cleanup();
                            $wire.markTimeout();
                        }
                    }, 1000);
                    const url = $wire.streamUrl;
                    if (url) {
                        this.es = new EventSource(url);
                        this.es.addEventListener('search_started', (e) => {
                            const data = JSON.parse(e.data);
                            this.currentAngle = data.angle;
                        });
                        this.es.addEventListener('search_completed', (e) => {
                            const data = JSON.parse(e.data);
                            this.angles.push({ angle: data.angle, count: data.results_count });
                            this.currentAngle = null;
                        });
                        this.es.addEventListener('completed', (e) => {
                            this.cleanup();
                            $wire.loadResult();
                        });
                        this.es.addEventListener('error', (e) => {
                            if (e.data) {
                                this.cleanup();
                                try {
                                    const data = JSON.parse(e.data);
                                    $wire.markError(data.message || null);
                                } catch {
                                    $wire.markError();
                                }
                            }
                        });
                        this.es.addEventListener('timeout', (e) => {
                            this.cleanup();
                            $wire.markTimeout();
                        });
                        this.es.onerror = () => {
                            this.cleanup();
                            $wire.loadResult();
                        };
                    }
                },
                cleanup() {
                    if (this.timerInterval) { clearInterval(this.timerInterval); this.timerInterval = null; }
                    if (this.es) { this.es.close(); this.es = null; }
                },
                destroy() { this.cleanup(); }
             }"
             x-on:livewire:navigating.window="cleanup()"
             class="bg-[var(--c-surface-card)] rounded-lg border border-[var(--c-border)] p-8 text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-2 border-[var(--c-border)] border-t-[var(--c-accent)] mb-4"></div>
            <p class="text-base font-medium text-[var(--c-text)]">Analisando angulos juridicos...</p>
            <p class="text-sm text-[var(--c-text-muted)] mt-2">
                O agente esta decompondo sua query em sub-buscas por angulo.
                Isso pode levar de 20 a 60 segundos.
            </p>

            {{-- Real-time angle chips --}}
            <div class="flex flex-wrap justify-center gap-1.5 mt-4 min-h-[28px]">
                <template x-for="a in angles" :key="a.angle">
                    <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-[var(--c-surface-raised)] text-[var(--c-text-secondary)] border border-[var(--c-border)]">
                        <span x-text="a.angle"></span>
                        <span class="ml-1.5 text-[var(--c-text-muted)] font-mono" x-text="a.count"></span>
                    </span>
                </template>
                <template x-if="currentAngle">
                    <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
                        <span x-text="currentAngle"></span>
                        <span class="ml-1.5">...</span>
                    </span>
                </template>
            </div>

            <p class="text-2xl font-mono text-[var(--c-text-secondary)] mt-4"
               x-text="Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0')">
            </p>
        </div>
    @endif

    {{-- Timeout State --}}
    @if($status === 'timeout')
        <div class="bg-amber-50 border border-amber-200 rounded-lg p-5">
            <h3 class="text-sm font-semibold text-amber-800">Tempo limite excedido</h3>
            <p class="text-sm text-amber-700 mt-1">A busca demorou mais de 10 minutos. Tente com uma query mais especifica ou use a busca direta.</p>
            <button wire:click="cancelSearch" class="mt-3 px-4 py-1.5 bg-amber-600 text-white rounded-md hover:bg-amber-700 text-sm font-medium transition-colors">
                Tentar novamente
            </button>
        </div>
    @endif

    {{-- Error State --}}
    @if($status === 'error')
        <div class="bg-red-50 border border-red-200 rounded-lg p-5">
            <h3 class="text-sm font-semibold text-red-800">Erro na busca</h3>
            <p class="text-sm text-red-700 mt-1">
                {{ $errorMessage ?? 'O processo terminou sem produzir resultados. Verifique os logs.' }}
            </p>
            <button wire:click="cancelSearch" class="mt-3 px-4 py-1.5 bg-[var(--c-accent-danger)] text-white rounded-md hover:opacity-90 text-sm font-medium transition-opacity">
                Tentar novamente
            </button>
        </div>
    @endif

    {{-- Results --}}
    @if($status === 'completed' && $decomposition)
        {{-- Decomposition chips --}}
        <div class="mb-5 flex flex-wrap gap-1.5">
            @foreach($decomposition['angles'] ?? [] as $angle)
                <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-[var(--c-surface-raised)] text-[var(--c-text-secondary)] border border-[var(--c-border)]">
                    {{ $angle['angle'] }}
                    <span class="ml-1.5 text-[var(--c-text-muted)] font-mono">{{ $angle['results_count'] }}</span>
                </span>
            @endforeach
        </div>

        {{-- Summary --}}
        <p class="mb-4 text-xs font-mono text-[var(--c-text-muted)]">
            {{ count($results ?? []) }} resultados | {{ $decomposition['rounds'] ?? '?' }} rounds
            @if($elapsedSeconds > 0)
                | {{ floor($elapsedSeconds / 60) }}m{{ $elapsedSeconds % 60 }}s
            @endif
        </p>

        {{-- Grouped results by angle --}}
        @php
            $grouped = collect($results ?? [])->groupBy('found_via');
            $angleMap = collect($decomposition['angles'] ?? [])->keyBy('query');
        @endphp

        @foreach($grouped as $via => $items)
            <div class="mb-8">
                <h3 class="angle-header text-sm font-semibold text-[var(--c-text)] mb-3 pb-2 border-b border-[var(--c-border)]">
                    {{ $angleMap[$via]['angle'] ?? $via }}
                    <span class="text-xs font-normal text-[var(--c-text-muted)] ml-2">({{ count($items) }})</span>
                </h3>

                <div class="space-y-3">
                    @foreach($items as $item)
                        @php
                            $rrf = $item['scores']['rrf'] ?? 0;
                            $rrfColor = $rrf >= 0.025 ? 'var(--c-accent-success)' : ($rrf >= 0.015 ? 'var(--c-accent-warning)' : 'var(--c-text-muted)');
                            $rrfPct = min($rrf / 0.035 * 100, 100);
                        @endphp
                        <div class="result-card bg-[var(--c-surface-card)] rounded-lg border border-[var(--c-border)] p-4">
                            <div class="flex items-start justify-between mb-2">
                                <div class="flex items-center gap-1.5 flex-wrap">
                                    @if(!empty($item['tipo']))
                                        <span class="px-2 py-0.5 rounded text-xs font-medium {{ ($item['tipo'] === 'ACORDAO' || $item['tipo'] === 'ACÓRDÃO') ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700' }}">
                                            {{ $item['tipo'] }}
                                        </span>
                                    @endif
                                    @if(!empty($item['classe']))
                                        <span class="bg-[var(--c-surface-raised)] text-[var(--c-text-secondary)] px-2 py-0.5 rounded text-xs font-medium">
                                            {{ $item['classe'] }}
                                        </span>
                                    @endif
                                    @if(!empty($item['processo']))
                                        @if(!empty($item['doc_id']))
                                            <a href="{{ route('search.document', $item['doc_id']) }}" target="_blank" class="text-sm text-[var(--c-text)] font-medium hover:text-[var(--c-accent)] hover:underline transition-colors">{{ $item['processo'] }}</a>
                                        @else
                                            <span class="text-sm text-[var(--c-text)] font-medium">{{ $item['processo'] }}</span>
                                        @endif
                                    @endif
                                </div>
                                @if($rrf > 0)
                                    <div class="flex items-center gap-2 ml-3 shrink-0">
                                        <div class="relevance-bar" style="width:36px"><div class="relevance-bar-fill" style="width:{{ $rrfPct }}%;background:{{ $rrfColor }}"></div></div>
                                        <span class="text-xs font-mono" style="color:{{ $rrfColor }}">{{ number_format($rrf, 4) }}</span>
                                    </div>
                                @endif
                            </div>

                            @if(!empty($item['content_preview']))
                                <p class="text-sm text-[var(--c-text-secondary)] leading-relaxed mb-2.5">
                                    {{ Str::limit($item['content_preview'], 300) }}
                                </p>
                            @endif

                            <div class="flex justify-between items-center text-xs text-[var(--c-text-muted)]">
                                <div class="flex gap-3">
                                    @if(!empty($item['ministro']))
                                        <span>{{ $item['ministro'] }}</span>
                                    @endif
                                    @if(!empty($item['orgao_julgador']))
                                        <span>{{ $item['orgao_julgador'] }}</span>
                                    @endif
                                    @if(!empty($item['data_publicacao']))
                                        <span>{{ $item['data_publicacao'] }}</span>
                                    @endif
                                </div>
                                <div class="flex items-center gap-3">
                                    @if(!empty($item['scores']['dense']) && !empty($item['scores']['sparse']))
                                        <span class="font-mono opacity-60">
                                            d:{{ number_format($item['scores']['dense'], 2) }}
                                            s:{{ number_format($item['scores']['sparse'], 2) }}
                                        </span>
                                    @endif
                                    @if(!empty($item['doc_id']))
                                        <a href="{{ route('search.document', $item['doc_id']) }}" target="_blank" class="text-[var(--c-accent)] hover:underline transition-colors font-medium">Ver inteiro teor</a>
                                    @endif
                                </div>
                            </div>
                        </div>
                    @endforeach
                </div>
            </div>
        @endforeach
    @endif
</div>

<div>
    {{-- Search Form --}}
    <form wire:submit="startSearch" class="mb-6">
        <div class="flex gap-2">
            <input
                type="text"
                wire:model="query"
                placeholder="Ex: dano moral negativacao indevida banco"
                class="flex-1 px-4 py-2.5 border border-navy-200 rounded-lg focus:ring-2 focus:ring-navy-400/40 focus:border-navy-400 text-navy-900 placeholder-navy-300 bg-white transition-colors"
                @if($status === 'searching') disabled @endif
                minlength="3"
                maxlength="500"
                required
            >
            @if($status === 'searching')
                <button
                    type="button"
                    wire:click="cancelSearch"
                    class="px-6 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium text-sm"
                >
                    Cancelar
                </button>
            @else
                <button
                    type="submit"
                    class="px-6 py-2.5 bg-navy-900 text-white rounded-lg hover:bg-navy-800 active:bg-navy-950 transition-colors font-medium text-sm"
                >
                    Decompor e Buscar
                </button>
            @endif
        </div>
        @error('query')
            <p class="mt-2 text-sm text-red-600">{{ $message }}</p>
        @enderror
    </form>

    {{-- Searching State --}}
    @if($status === 'searching')
        <div wire:poll.3s="checkResult"
             x-data="{ seconds: {{ $elapsedSeconds }}, interval: null }"
             x-init="interval = setInterval(() => seconds++, 1000)"
             x-on:livewire:navigating.window="clearInterval(interval)"
             class="bg-white rounded-lg border border-navy-100 p-8 text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-2 border-navy-200 border-t-navy-600 mb-4"></div>
            <p class="text-base font-medium text-navy-800">Analisando angulos juridicos...</p>
            <p class="text-sm text-navy-400 mt-2">
                O agente esta decompondo sua query em sub-buscas por angulo.
                Isso pode levar de 20 a 60 segundos.
            </p>
            <p class="text-2xl font-mono text-navy-600 mt-4"
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
            <p class="text-sm text-red-700 mt-1">O agente retornou um resultado invalido. Tente novamente.</p>
            <button wire:click="cancelSearch" class="mt-3 px-4 py-1.5 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm font-medium transition-colors">
                Tentar novamente
            </button>
        </div>
    @endif

    {{-- Results --}}
    @if($status === 'completed' && $decomposition)
        {{-- Decomposition chips --}}
        <div class="mb-5 flex flex-wrap gap-1.5">
            @foreach($decomposition['angles'] ?? [] as $angle)
                <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-navy-50 text-navy-700 border border-navy-100">
                    {{ $angle['angle'] }}
                    <span class="ml-1.5 text-navy-400 font-mono">{{ $angle['results_count'] }}</span>
                </span>
            @endforeach
        </div>

        {{-- Summary --}}
        <p class="mb-4 text-xs font-mono text-navy-400">
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
                <h3 class="angle-header text-sm font-semibold text-navy-800 mb-3 pb-2 border-b border-navy-100">
                    {{ $angleMap[$via]['angle'] ?? $via }}
                    <span class="text-xs font-normal text-navy-400 ml-2">({{ count($items) }})</span>
                </h3>

                <div class="space-y-2.5">
                    @foreach($items as $item)
                        @php
                            $rrf = $item['scores']['rrf'] ?? 0;
                            $rrfColor = $rrf >= 0.025 ? '#16a34a' : ($rrf >= 0.015 ? '#d97706' : '#9fb3c8');
                            $rrfPct = min($rrf / 0.035 * 100, 100);
                        @endphp
                        <div class="result-card bg-white rounded-lg border border-navy-100 p-4">
                            <div class="flex items-start justify-between mb-2">
                                <div class="flex items-center gap-1.5 flex-wrap">
                                    @if(!empty($item['tipo']))
                                        <span class="px-2 py-0.5 rounded text-xs font-medium {{ ($item['tipo'] === 'ACORDAO' || $item['tipo'] === 'ACÓRDÃO') ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700' }}">
                                            {{ $item['tipo'] }}
                                        </span>
                                    @endif
                                    @if(!empty($item['classe']))
                                        <span class="bg-navy-50 text-navy-600 px-2 py-0.5 rounded text-xs font-medium">
                                            {{ $item['classe'] }}
                                        </span>
                                    @endif
                                    @if(!empty($item['processo']))
                                        @if(!empty($item['doc_id']))
                                            <a href="{{ route('search.document', $item['doc_id']) }}" class="text-sm text-navy-800 font-medium hover:text-navy-600 hover:underline transition-colors">{{ $item['processo'] }}</a>
                                        @else
                                            <span class="text-sm text-navy-700 font-medium">{{ $item['processo'] }}</span>
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
                                <p class="text-sm text-navy-700 leading-relaxed mb-2.5">
                                    {{ Str::limit($item['content_preview'], 300) }}
                                </p>
                            @endif

                            <div class="flex justify-between items-center text-xs text-navy-300">
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
                                        <span class="font-mono text-navy-300/70">
                                            d:{{ number_format($item['scores']['dense'], 2) }}
                                            s:{{ number_format($item['scores']['sparse'], 2) }}
                                        </span>
                                    @endif
                                    @if(!empty($item['doc_id']))
                                        <a href="{{ route('search.document', $item['doc_id']) }}" class="text-navy-500 hover:text-navy-700 hover:underline transition-colors font-medium">Ver inteiro teor</a>
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

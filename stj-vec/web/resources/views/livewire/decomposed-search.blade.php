<div>
    {{-- Search Form --}}
    <form wire:submit="startSearch" class="mb-6">
        <div class="flex gap-3">
            <input
                type="text"
                wire:model="query"
                placeholder="Ex: dano moral negativacao indevida banco"
                class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy-500 focus:border-navy-500 text-gray-800 placeholder-gray-400"
                @if($status === 'searching') disabled @endif
                minlength="3"
                maxlength="500"
                required
            >
            @if($status === 'searching')
                <button
                    type="button"
                    wire:click="cancelSearch"
                    class="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                >
                    Cancelar
                </button>
            @else
                <button
                    type="submit"
                    class="px-6 py-3 bg-navy-900 text-white rounded-lg hover:bg-navy-800 transition-colors font-medium"
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
        <div wire:poll.3s="checkResult" class="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
            <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-navy-200 border-t-navy-600 mb-4"></div>
            <p class="text-lg font-medium text-gray-700">Analisando angulos juridicos...</p>
            <p class="text-sm text-gray-500 mt-2">
                O agente esta decompondo sua query em sub-buscas por angulo.
                Isso pode levar de 2 a 7 minutos.
            </p>
            <p class="text-2xl font-mono text-navy-600 mt-4">
                {{ floor($elapsedSeconds / 60) }}:{{ str_pad($elapsedSeconds % 60, 2, '0', STR_PAD_LEFT) }}
            </p>
        </div>
    @endif

    {{-- Timeout State --}}
    @if($status === 'timeout')
        <div class="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <h3 class="text-lg font-medium text-amber-800">Tempo limite excedido</h3>
            <p class="text-amber-700 mt-1">A busca demorou mais de 10 minutos. Tente com uma query mais especifica ou use a busca direta.</p>
            <button wire:click="cancelSearch" class="mt-3 px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700 text-sm">
                Tentar novamente
            </button>
        </div>
    @endif

    {{-- Error State --}}
    @if($status === 'error')
        <div class="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 class="text-lg font-medium text-red-800">Erro na busca</h3>
            <p class="text-red-700 mt-1">O agente retornou um resultado invalido. Tente novamente.</p>
            <button wire:click="cancelSearch" class="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm">
                Tentar novamente
            </button>
        </div>
    @endif

    {{-- Results --}}
    @if($status === 'completed' && $decomposition)
        {{-- Decomposition chips --}}
        <div class="mb-6 flex flex-wrap gap-2">
            @foreach($decomposition['angles'] ?? [] as $angle)
                <span class="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-navy-100 text-navy-800">
                    {{ $angle['angle'] }}
                    <span class="ml-1.5 text-xs text-navy-500">({{ $angle['results_count'] }})</span>
                </span>
            @endforeach
        </div>

        {{-- Summary --}}
        <div class="mb-4 text-sm text-gray-500">
            {{ count($results ?? []) }} resultados em {{ $decomposition['rounds'] ?? '?' }} rounds
            @if($elapsedSeconds > 0)
                -- {{ floor($elapsedSeconds / 60) }}m{{ $elapsedSeconds % 60 }}s
            @endif
        </div>

        {{-- Grouped results by angle --}}
        @php
            $grouped = collect($results ?? [])->groupBy('found_via');
            $angleMap = collect($decomposition['angles'] ?? [])->keyBy('query');
        @endphp

        @foreach($grouped as $via => $items)
            <div class="mb-8">
                <h3 class="text-lg font-semibold text-navy-900 mb-3 border-b border-gray-200 pb-2">
                    {{ $angleMap[$via]['angle'] ?? $via }}
                    <span class="text-sm font-normal text-gray-500 ml-2">({{ count($items) }} resultados)</span>
                </h3>

                <div class="space-y-3">
                    @foreach($items as $item)
                        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
                            <div class="flex items-start justify-between mb-2">
                                <div class="flex items-center gap-2 flex-wrap">
                                    @if(!empty($item['tipo']))
                                        <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded
                                            {{ $item['tipo'] === 'ACORDAO' || $item['tipo'] === 'ACÓRDÃO' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700' }}">
                                            {{ $item['tipo'] }}
                                        </span>
                                    @endif
                                    @if(!empty($item['classe']))
                                        <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded bg-gray-100 text-gray-600">
                                            {{ $item['classe'] }}
                                        </span>
                                    @endif
                                    @if(!empty($item['processo']))
                                        <span class="text-sm text-gray-700 font-medium">{{ $item['processo'] }}</span>
                                    @endif
                                </div>
                                @if(!empty($item['scores']['rrf']))
                                    <span class="text-sm font-mono font-medium {{ $item['scores']['rrf'] >= 0.7 ? 'text-green-600' : ($item['scores']['rrf'] >= 0.4 ? 'text-yellow-600' : 'text-gray-500') }}">
                                        {{ number_format($item['scores']['rrf'], 2) }}
                                    </span>
                                @endif
                            </div>

                            @if(!empty($item['content_preview']))
                                <p class="text-sm text-gray-600 leading-relaxed mb-3">
                                    {{ Str::limit($item['content_preview'], 300) }}
                                </p>
                            @endif

                            <div class="flex items-center gap-4 text-xs text-gray-400">
                                @if(!empty($item['ministro']))
                                    <span>{{ $item['ministro'] }}</span>
                                @endif
                                @if(!empty($item['orgao_julgador']))
                                    <span>{{ $item['orgao_julgador'] }}</span>
                                @endif
                                @if(!empty($item['data_publicacao']))
                                    <span>{{ $item['data_publicacao'] }}</span>
                                @endif
                                @if(!empty($item['scores']['dense']) && !empty($item['scores']['sparse']))
                                    <span class="ml-auto font-mono">
                                        d:{{ number_format($item['scores']['dense'], 2) }}
                                        s:{{ number_format($item['scores']['sparse'], 2) }}
                                    </span>
                                @endif
                            </div>
                        </div>
                    @endforeach
                </div>
            </div>
        @endforeach
    @endif
</div>

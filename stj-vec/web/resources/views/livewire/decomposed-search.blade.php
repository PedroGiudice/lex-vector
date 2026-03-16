<div>
    {{-- Search Form --}}
    <form wire:submit="startSearch" class="mb-6">
        <flux:input.group>
            <flux:input
                type="text"
                wire:model="query"
                placeholder="Ex: dano moral negativacao indevida banco"
                @if($status === 'searching') disabled @endif
                minlength="3"
                maxlength="500"
                required
            />
            @if($status === 'searching')
                <flux:button type="button" wire:click="cancelSearch" variant="danger">
                    Cancelar
                </flux:button>
            @else
                <flux:button type="submit" variant="primary">
                    Decompor e Buscar
                </flux:button>
            @endif
        </flux:input.group>
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
             class="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
            <flux:icon.loading class="size-10 mx-auto mb-4 text-navy-600" />
            <p class="text-lg font-medium text-gray-700">Analisando angulos juridicos...</p>
            <p class="text-sm text-gray-500 mt-2">
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
        <div class="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <flux:heading size="sm" class="text-amber-800">Tempo limite excedido</flux:heading>
            <p class="text-amber-700 mt-1">A busca demorou mais de 10 minutos. Tente com uma query mais especifica ou use a busca direta.</p>
            <flux:button wire:click="cancelSearch" variant="filled" size="sm" class="mt-3">
                Tentar novamente
            </flux:button>
        </div>
    @endif

    {{-- Error State --}}
    @if($status === 'error')
        <div class="bg-red-50 border border-red-200 rounded-lg p-6">
            <flux:heading size="sm" class="text-red-800">Erro na busca</flux:heading>
            <p class="text-red-700 mt-1">O agente retornou um resultado invalido. Tente novamente.</p>
            <flux:button wire:click="cancelSearch" variant="danger" size="sm" class="mt-3">
                Tentar novamente
            </flux:button>
        </div>
    @endif

    {{-- Results --}}
    @if($status === 'completed' && $decomposition)
        {{-- Decomposition chips --}}
        <div class="mb-6 flex flex-wrap gap-2">
            @foreach($decomposition['angles'] ?? [] as $angle)
                <flux:badge color="indigo" size="sm">
                    {{ $angle['angle'] }}
                    <flux:badge.close class="pointer-events-none opacity-0 w-0" />
                    <span class="ml-1 text-xs opacity-70">({{ $angle['results_count'] }})</span>
                </flux:badge>
            @endforeach
        </div>

        {{-- Summary --}}
        <p class="mb-4 text-sm text-gray-500">
            {{ count($results ?? []) }} resultados em {{ $decomposition['rounds'] ?? '?' }} rounds
            @if($elapsedSeconds > 0)
                -- {{ floor($elapsedSeconds / 60) }}m{{ $elapsedSeconds % 60 }}s
            @endif
        </p>

        {{-- Grouped results by angle --}}
        @php
            $grouped = collect($results ?? [])->groupBy('found_via');
            $angleMap = collect($decomposition['angles'] ?? [])->keyBy('query');
        @endphp

        @foreach($grouped as $via => $items)
            <div class="mb-8">
                <flux:heading size="lg" class="mb-3 border-b border-gray-200 pb-2">
                    {{ $angleMap[$via]['angle'] ?? $via }}
                    <span class="text-sm font-normal text-gray-500 ml-2">({{ count($items) }} resultados)</span>
                </flux:heading>

                <div class="space-y-3">
                    @foreach($items as $item)
                        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
                            <div class="flex items-start justify-between mb-2">
                                <div class="flex items-center gap-2 flex-wrap">
                                    @if(!empty($item['tipo']))
                                        <flux:badge size="sm" :color="($item['tipo'] === 'ACORDAO' || $item['tipo'] === 'ACÓRDÃO') ? 'blue' : 'amber'">
                                            {{ $item['tipo'] }}
                                        </flux:badge>
                                    @endif
                                    @if(!empty($item['classe']))
                                        <flux:badge size="sm" color="zinc">{{ $item['classe'] }}</flux:badge>
                                    @endif
                                    @if(!empty($item['processo']))
                                        @if(!empty($item['doc_id']))
                                            <a href="{{ route('search.document', $item['doc_id']) }}" class="text-sm text-navy-700 font-medium hover:text-navy-500 hover:underline">{{ $item['processo'] }}</a>
                                        @else
                                            <span class="text-sm text-gray-700 font-medium">{{ $item['processo'] }}</span>
                                        @endif
                                    @endif
                                </div>
                                @if(!empty($item['scores']['rrf']))
                                    <span class="text-sm font-mono font-medium {{ $item['scores']['rrf'] >= 0.025 ? 'text-green-600' : ($item['scores']['rrf'] >= 0.015 ? 'text-yellow-600' : 'text-gray-500') }}">
                                        #{{ $loop->iteration }} <span class="opacity-60">{{ number_format($item['scores']['rrf'], 4) }}</span>
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
                                    <span class="font-mono">
                                        d:{{ number_format($item['scores']['dense'], 2) }}
                                        s:{{ number_format($item['scores']['sparse'], 2) }}
                                    </span>
                                @endif
                                @if(!empty($item['doc_id']))
                                    <a href="{{ route('search.document', $item['doc_id']) }}" class="ml-auto text-navy-500 hover:text-navy-700 hover:underline">Ver inteiro teor</a>
                                @endif
                            </div>
                        </div>
                    @endforeach
                </div>
            </div>
        @endforeach
    @endif
</div>

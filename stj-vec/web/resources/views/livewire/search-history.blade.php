<div class="h-full flex flex-col" wire:poll.30s>
    {{-- Header --}}
    <div class="px-4 pt-4 pb-3 border-b border-slate-100">
        <h2 class="text-[11px] font-semibold text-slate-400 uppercase tracking-widest">Historico</h2>
    </div>

    {{-- List --}}
    <nav class="flex-1 overflow-y-auto px-2 py-2">
        @php
            $grouped = $jobs->groupBy(fn ($job) => $job->created_at->isToday()
                ? 'Hoje'
                : ($job->created_at->isYesterday() ? 'Ontem' : $job->created_at->format('d/m'))
            );
        @endphp

        @forelse($grouped as $label => $group)
            {{-- Date group label --}}
            <div class="px-2 pt-3 pb-1.5 first:pt-1">
                <span class="text-[10px] font-medium text-slate-300 uppercase tracking-wider">{{ $label }}</span>
            </div>

            @foreach($group as $job)
                @php
                    $isCompleted = $job->status === 'completed';
                    $isError = $job->status === 'error';
                    $isRunning = $job->status === 'running';
                @endphp
                <button
                    @if($isCompleted) wire:click="loadJob('{{ $job->id }}')" @endif
                    class="w-full text-left px-3 py-2 rounded-md transition-all duration-150 group relative
                        {{ $isCompleted ? 'hover:bg-slate-50 cursor-pointer' : '' }}
                        {{ $isRunning ? 'bg-amber-50/50' : '' }}
                        {{ $isError ? 'opacity-50' : '' }}
                        {{ !$isCompleted ? 'cursor-default' : '' }}"
                    @if(!$isCompleted) disabled @endif
                >
                    {{-- Query text --}}
                    <div class="flex items-start gap-2">
                        {{-- Status indicator --}}
                        <div class="mt-1.5 shrink-0">
                            @if($isCompleted)
                                <svg class="w-3.5 h-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            @elseif($isRunning)
                                <svg class="w-3.5 h-3.5 text-amber-500 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                                </svg>
                            @elseif($isError)
                                <svg class="w-3.5 h-3.5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            @else
                                <div class="w-3.5 h-3.5 flex items-center justify-center">
                                    <div class="w-1.5 h-1.5 rounded-full bg-slate-300"></div>
                                </div>
                            @endif
                        </div>

                        <div class="min-w-0 flex-1">
                            <p class="text-[13px] text-slate-600 leading-snug truncate group-hover:text-slate-900 transition-colors">
                                {{ Str::limit($job->query, 36) }}
                            </p>

                            {{-- Meta row --}}
                            <div class="flex items-center gap-2 mt-1">
                                @if($isCompleted && $job->total_results)
                                    <span class="text-[10px] font-medium text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                                        {{ $job->total_results }} res.
                                    </span>
                                @endif

                                @if($job->duration_ms)
                                    <span class="text-[10px] text-slate-300 font-mono">
                                        {{ round($job->duration_ms / 1000) }}s
                                    </span>
                                @endif

                                <span class="text-[10px] text-slate-300 ml-auto tabular-nums">
                                    {{ $job->created_at->format('H:i') }}
                                </span>
                            </div>
                        </div>
                    </div>
                </button>
            @endforeach
        @empty
            <div class="px-3 py-8 text-center">
                <svg class="w-8 h-8 text-slate-200 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p class="text-xs text-slate-400">Nenhuma busca ainda</p>
                <p class="text-[10px] text-slate-300 mt-0.5">Suas buscas aparecerao aqui</p>
            </div>
        @endforelse
    </nav>
</div>

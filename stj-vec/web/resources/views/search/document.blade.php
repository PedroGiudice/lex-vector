@extends('layouts.app')

@section('title', ($document['processo'] ?? 'Documento') . ' - STJ-Vec')

@section('content')
<div class="max-w-4xl mx-auto">
    {{-- Voltar --}}
    <div class="mb-5">
        <a
            href="{{ route('search.index') }}"
            class="inline-flex items-center text-sm text-[var(--c-text-muted)] hover:text-[var(--c-text)] transition-colors font-medium"
        >
            <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Voltar para a busca
        </a>
    </div>

    {{-- Metadados --}}
    <div class="bg-[var(--c-surface-card)] rounded-lg border border-[var(--c-border)] p-5 mb-5">
        <div class="flex items-start justify-between mb-4">
            <h1 class="text-lg font-semibold text-[var(--c-text)]">
                {{ $document['processo'] ?? 'Processo nao identificado' }}
            </h1>
            @if(!empty($document['tipo']))
                <span class="px-2.5 py-0.5 rounded text-xs font-medium {{ ($document['tipo'] === 'ACORDAO' || $document['tipo'] === 'ACÓRDÃO') ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700' }}">
                    {{ $document['tipo'] }}
                </span>
            @endif
        </div>

        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
            @if(!empty($document['classe']))
                <div>
                    <dt class="text-xs text-[var(--c-text-muted)]">Classe</dt>
                    <dd class="font-medium text-[var(--c-text)]">{{ $document['classe'] }}</dd>
                </div>
            @endif
            @if(!empty($document['ministro']))
                <div>
                    <dt class="text-xs text-[var(--c-text-muted)]">Ministro Relator</dt>
                    <dd class="font-medium text-[var(--c-text)]">{{ $document['ministro'] }}</dd>
                </div>
            @endif
            @if(!empty($document['orgao_julgador']))
                <div>
                    <dt class="text-xs text-[var(--c-text-muted)]">Orgao Julgador</dt>
                    <dd class="font-medium text-[var(--c-text)]">{{ $document['orgao_julgador'] }}</dd>
                </div>
            @endif
            @if(!empty($document['data_publicacao']))
                <div>
                    <dt class="text-xs text-[var(--c-text-muted)]">Data de Publicacao</dt>
                    <dd class="font-medium text-[var(--c-text)]">{{ $document['data_publicacao'] }}</dd>
                </div>
            @endif
        </dl>
    </div>

    {{-- Corpo do documento --}}
    <div class="bg-[var(--c-surface-card)] rounded-lg border border-[var(--c-border)] p-6">
        <div class="flex items-center justify-between mb-5 pb-3 border-b border-[var(--c-border)]">
            <h2 class="text-sm font-semibold text-[var(--c-text)]">
                Inteiro Teor
            </h2>
            <span class="text-xs text-[var(--c-text-muted)] font-mono">{{ $chunks->count() }} partes</span>
        </div>

        <div class="document-prose">
            @php
                $currentSection = null;
                $sectionLabels = [
                    'ementa' => 'Ementa',
                    'acordao' => 'Acordao',
                    'relatorio' => 'Relatorio',
                    'voto' => 'Voto',
                    'decisao' => 'Decisao',
                ];
            @endphp

            @foreach($chunks as $chunk)
                @php
                    $section = $chunk['section'] ?? $chunk['secao'] ?? null;
                @endphp

                @if($section && $section !== $currentSection)
                    @php $currentSection = $section; @endphp
                    <div class="mt-6 mb-3 first:mt-0">
                        <span class="section-label">{{ $sectionLabels[$section] ?? ucfirst($section) }}</span>
                    </div>
                @endif

                <div class="chunk-section">
                    <p>{!! nl2br(e($chunk['content'])) !!}</p>
                </div>
            @endforeach
        </div>
    </div>
</div>
@endsection

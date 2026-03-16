@extends('layouts.app')

@section('title', ($document['processo'] ?? 'Documento') . ' - STJ-Vec')

@section('content')
<div class="max-w-4xl mx-auto">
    {{-- Voltar --}}
    <div class="mb-5">
        <a
            href="{{ route('search.index') }}"
            class="inline-flex items-center text-sm text-navy-500 hover:text-navy-700 transition-colors font-medium"
        >
            <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Voltar para a busca
        </a>
    </div>

    {{-- Metadados --}}
    <div class="bg-white rounded-lg border border-navy-100 p-5 mb-5">
        <div class="flex items-start justify-between mb-4">
            <h1 class="text-lg font-semibold text-navy-900">
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
                    <dt class="text-xs text-navy-400">Classe</dt>
                    <dd class="font-medium text-navy-800">{{ $document['classe'] }}</dd>
                </div>
            @endif
            @if(!empty($document['ministro']))
                <div>
                    <dt class="text-xs text-navy-400">Ministro Relator</dt>
                    <dd class="font-medium text-navy-800">{{ $document['ministro'] }}</dd>
                </div>
            @endif
            @if(!empty($document['orgao_julgador']))
                <div>
                    <dt class="text-xs text-navy-400">Orgao Julgador</dt>
                    <dd class="font-medium text-navy-800">{{ $document['orgao_julgador'] }}</dd>
                </div>
            @endif
            @if(!empty($document['data_publicacao']))
                <div>
                    <dt class="text-xs text-navy-400">Data de Publicacao</dt>
                    <dd class="font-medium text-navy-800">{{ $document['data_publicacao'] }}</dd>
                </div>
            @endif
        </dl>
    </div>

    {{-- Corpo do documento --}}
    <div class="bg-white rounded-lg border border-navy-100 p-5">
        <h2 class="text-sm font-semibold text-navy-800 mb-4 pb-3 border-b border-navy-100">
            Inteiro Teor
            <span class="text-xs font-normal text-navy-400 font-mono ml-2">{{ $chunks->count() }} partes</span>
        </h2>

        <div class="prose prose-sm max-w-none text-navy-700 leading-relaxed">
            @foreach($chunks as $chunk)
                <p>{{ $chunk['content'] }}</p>
            @endforeach
        </div>
    </div>
</div>
@endsection

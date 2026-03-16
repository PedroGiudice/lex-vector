@extends('layouts.app')

@section('title', ($document['processo'] ?? 'Documento') . ' - STJ-Vec')

@section('content')
<div class="max-w-4xl mx-auto">
    {{-- Voltar --}}
    <div class="mb-6">
        <a
            href="{{ route('search.index') }}"
            class="inline-flex items-center text-sm text-navy-600 hover:text-navy-800 transition-colors"
        >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Voltar para a busca
        </a>
    </div>

    {{-- Metadados --}}
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-6">
        <div class="flex items-start justify-between mb-4">
            <h1 class="text-xl font-semibold text-navy-900">
                {{ $document['processo'] ?? 'Processo nao identificado' }}
            </h1>
            @if(!empty($document['tipo']))
                <span class="inline-flex px-3 py-1 text-xs font-medium rounded
                    {{ ($document['tipo'] === 'ACORDAO' || $document['tipo'] === 'ACÓRDÃO') ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700' }}">
                    {{ $document['tipo'] }}
                </span>
            @endif
        </div>

        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
            @if(!empty($document['classe']))
                <div>
                    <dt class="text-gray-500">Classe</dt>
                    <dd class="font-medium text-gray-800">{{ $document['classe'] }}</dd>
                </div>
            @endif
            @if(!empty($document['ministro']))
                <div>
                    <dt class="text-gray-500">Ministro Relator</dt>
                    <dd class="font-medium text-gray-800">{{ $document['ministro'] }}</dd>
                </div>
            @endif
            @if(!empty($document['orgao_julgador']))
                <div>
                    <dt class="text-gray-500">Orgao Julgador</dt>
                    <dd class="font-medium text-gray-800">{{ $document['orgao_julgador'] }}</dd>
                </div>
            @endif
            @if(!empty($document['data_publicacao']))
                <div>
                    <dt class="text-gray-500">Data de Publicacao</dt>
                    <dd class="font-medium text-gray-800">{{ $document['data_publicacao'] }}</dd>
                </div>
            @endif
        </dl>
    </div>

    {{-- Corpo do documento --}}
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h2 class="text-lg font-semibold text-navy-900 mb-4 pb-3 border-b border-gray-200">
            Inteiro Teor
            <span class="text-sm font-normal text-gray-500 ml-2">({{ $chunks->count() }} partes)</span>
        </h2>

        <div class="prose prose-sm max-w-none text-gray-700 leading-relaxed">
            @foreach($chunks as $chunk)
                <p>{{ $chunk['content'] }}</p>
            @endforeach
        </div>
    </div>
</div>
@endsection

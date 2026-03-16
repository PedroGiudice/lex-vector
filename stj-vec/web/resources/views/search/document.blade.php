@extends('layouts.app')

@section('title', ($document['processo'] ?? 'Documento') . ' - STJ-Vec')

@section('content')
<div class="max-w-4xl mx-auto">
    {{-- Voltar --}}
    <div class="mb-6">
        <flux:button variant="subtle" size="sm" icon="arrow-left" :href="route('search.index')">
            Voltar para a busca
        </flux:button>
    </div>

    {{-- Metadados --}}
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-6">
        <div class="flex items-start justify-between mb-4">
            <flux:heading size="xl">
                {{ $document['processo'] ?? 'Processo nao identificado' }}
            </flux:heading>
            @if(!empty($document['tipo']))
                <flux:badge :color="($document['tipo'] === 'ACORDAO' || $document['tipo'] === 'ACÓRDÃO') ? 'blue' : 'amber'">
                    {{ $document['tipo'] }}
                </flux:badge>
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
        <flux:heading size="lg" class="mb-4 pb-3 border-b border-gray-200">
            Inteiro Teor
            <span class="text-sm font-normal text-gray-500 ml-2">({{ $chunks->count() }} partes)</span>
        </flux:heading>

        <div class="prose prose-sm max-w-none text-gray-700 leading-relaxed">
            @foreach($chunks as $chunk)
                <p>{{ $chunk['content'] }}</p>
            @endforeach
        </div>
    </div>
</div>
@endsection

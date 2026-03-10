@extends('layouts.app')

@section('title', 'Busca - STJ-Vec')

@section('content')
<div id="app">
    {{-- Formulario de busca --}}
    <form id="search-form" class="space-y-4">
        <div class="flex gap-3">
            <input
                type="text"
                id="query"
                name="query"
                placeholder="Ex: dano moral bancario, revisao contratual, responsabilidade civil objetiva..."
                class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                required
                minlength="3"
                autofocus
            >
            <button
                type="submit"
                id="btn-search"
                class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
                Buscar
            </button>
        </div>

        {{-- Filtros colapsaveis --}}
        <details class="bg-white rounded-lg border border-gray-200 p-4">
            <summary class="cursor-pointer text-sm font-medium text-gray-600">Filtros avancados</summary>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div>
                    <label class="block text-sm text-gray-600 mb-1">Ministro</label>
                    <select name="filters[ministro]" class="w-full px-3 py-2 border rounded-md text-sm">
                        <option value="">Todos</option>
                        @foreach($filters['ministros'] ?? [] as $m)
                            <option value="{{ $m }}">{{ $m }}</option>
                        @endforeach
                    </select>
                </div>
                <div>
                    <label class="block text-sm text-gray-600 mb-1">Tipo</label>
                    <select name="filters[tipo]" class="w-full px-3 py-2 border rounded-md text-sm">
                        <option value="">Todos</option>
                        @foreach($filters['tipos'] ?? [] as $t)
                            <option value="{{ $t }}">{{ $t }}</option>
                        @endforeach
                    </select>
                </div>
                <div>
                    <label class="block text-sm text-gray-600 mb-1">Classe</label>
                    <select name="filters[classe]" class="w-full px-3 py-2 border rounded-md text-sm">
                        <option value="">Todos</option>
                        @foreach($filters['classes'] ?? [] as $c)
                            <option value="{{ $c }}">{{ $c }}</option>
                        @endforeach
                    </select>
                </div>
                <div>
                    <label class="block text-sm text-gray-600 mb-1">Orgao Julgador</label>
                    <select name="filters[orgao_julgador]" class="w-full px-3 py-2 border rounded-md text-sm">
                        <option value="">Todos</option>
                        @foreach($filters['orgaos_julgadores'] ?? [] as $o)
                            <option value="{{ $o }}">{{ $o }}</option>
                        @endforeach
                    </select>
                </div>
                <div>
                    <label class="block text-sm text-gray-600 mb-1">Data de</label>
                    <input type="date" name="filters[data_from]" class="w-full px-3 py-2 border rounded-md text-sm">
                </div>
                <div>
                    <label class="block text-sm text-gray-600 mb-1">Data ate</label>
                    <input type="date" name="filters[data_to]" class="w-full px-3 py-2 border rounded-md text-sm">
                </div>
            </div>
        </details>
    </form>

    {{-- Indicador de carregamento --}}
    <div id="loading" class="hidden mt-8 text-center text-gray-500">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-blue-600"></div>
        <span class="ml-2">Buscando...</span>
    </div>

    {{-- Info da query --}}
    <div id="query-info" class="hidden mt-6 bg-white rounded-lg border border-gray-200 p-3 text-xs text-gray-500 flex gap-4 flex-wrap"></div>

    {{-- Resultados --}}
    <div id="results" class="mt-6 space-y-4"></div>
</div>

<script>
const form = document.getElementById('search-form');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const queryInfo = document.getElementById('query-info');
const btnSearch = document.getElementById('btn-search');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const query = formData.get('query')?.trim();
    if (!query || query.length < 3) return;

    const payload = { query };

    const limit = formData.get('limit');
    if (limit) payload.limit = parseInt(limit);

    const filters = {};
    for (const [key, value] of formData.entries()) {
        const match = key.match(/^filters\[(\w+)\]$/);
        if (match && value) {
            filters[match[1]] = value;
        }
    }
    if (Object.keys(filters).length > 0) payload.filters = filters;

    loading.classList.remove('hidden');
    results.innerHTML = '';
    queryInfo.classList.add('hidden');
    btnSearch.disabled = true;

    try {
        const response = await fetch('{{ route("search.query") }}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
                'Accept': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            results.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">${data.error || 'Erro na busca'}</div>`;
            return;
        }

        if (data.query_info) {
            queryInfo.innerHTML = `
                <span>Embedding: ${data.query_info.embedding_ms}ms</span>
                <span>Busca: ${data.query_info.search_ms}ms</span>
                <span>Metadados: ${data.query_info.metadata_ms}ms</span>
                <span>Total: ${data.query_info.total_ms}ms</span>
                <span>Dense: ${data.query_info.dense_candidates}</span>
                <span>Sparse: ${data.query_info.sparse_candidates}</span>
                <span>Resultados: ${data.query_info.post_filter_count}/${data.query_info.pre_filter_count}</span>
            `;
            queryInfo.classList.remove('hidden');
        }

        if (!data.results || data.results.length === 0) {
            results.innerHTML = '<div class="text-center text-gray-500 py-8">Nenhum resultado encontrado.</div>';
            return;
        }

        results.innerHTML = data.results.map((item, i) => `
            <div class="bg-white rounded-lg border border-gray-200 p-5 hover:border-gray-300 transition">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex gap-2 text-xs text-gray-500 flex-wrap">
                        <span class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded">${item.classe}</span>
                        <span class="bg-green-50 text-green-700 px-2 py-0.5 rounded">${item.tipo}</span>
                        <span>${item.processo}</span>
                    </div>
                    <span class="text-xs text-gray-400 whitespace-nowrap ml-2">RRF: ${item.scores.rrf.toFixed(4)}</span>
                </div>
                <p class="text-sm text-gray-800 leading-relaxed mb-3 whitespace-pre-wrap">${highlightTerms(item.content, query)}</p>
                <div class="flex justify-between items-center text-xs text-gray-500">
                    <div class="flex gap-3">
                        <span>Min. ${item.ministro}</span>
                        <span>${item.orgao_julgador}</span>
                        <span>${item.data_publicacao}</span>
                    </div>
                    <div class="flex gap-2">
                        <span title="Dense score">D: ${item.scores.dense.toFixed(3)}</span>
                        <span title="Sparse score">S: ${item.scores.sparse.toFixed(1)}</span>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (err) {
        results.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Erro de conexao: ${err.message}</div>`;
    } finally {
        loading.classList.add('hidden');
        btnSearch.disabled = false;
    }
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function highlightTerms(text, query) {
    const escaped = escapeHtml(text);
    const terms = query.split(/\s+/).filter(t => t.length >= 3);
    if (terms.length === 0) return escaped;
    const pattern = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
    const regex = new RegExp(`(${pattern})`, 'gi');
    return escaped.replace(regex, '<mark class="bg-yellow-200 rounded px-0.5">$1</mark>');
}
</script>
@endsection

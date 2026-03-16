@extends('layouts.app')

@section('title', 'Busca - STJ-Vec')

@section('content')
<div x-data="{ tab: 'direct' }">
    {{-- Tabs --}}
    <div class="flex border-b border-gray-200 mb-6">
        <button
            @click="tab = 'direct'"
            :class="tab === 'direct' ? 'border-navy-600 text-navy-900' : 'border-transparent text-gray-500 hover:text-gray-700'"
            class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
        >
            Busca Direta
        </button>
        <button
            @click="tab = 'decomposed'"
            :class="tab === 'decomposed' ? 'border-navy-600 text-navy-900' : 'border-transparent text-gray-500 hover:text-gray-700'"
            class="px-6 py-3 text-sm font-medium border-b-2 transition-colors"
        >
            Busca Decomposta
        </button>
    </div>

    {{-- Tab: Busca Direta --}}
    <div x-show="tab === 'direct'" x-cloak>
        <div class="flex gap-6">
            {{-- Sidebar de filtros --}}
            <aside class="hidden lg:block w-64 flex-shrink-0">
                <div class="bg-white rounded-lg border border-gray-200 p-4 sticky top-6 space-y-4">
                    <flux:heading size="sm">Filtros</flux:heading>
                    <flux:select id="filter-tipo" placeholder="Tipo" size="sm">
                        <flux:select.option value="">Todos</flux:select.option>
                        @foreach($filters['tipos'] ?? [] as $t)
                            <flux:select.option value="{{ $t }}">{{ $t }}</flux:select.option>
                        @endforeach
                    </flux:select>
                    <flux:select id="filter-classe" placeholder="Classe" size="sm">
                        <flux:select.option value="">Todas</flux:select.option>
                        @foreach($filters['classes'] ?? [] as $c)
                            <flux:select.option value="{{ $c }}">{{ $c }}</flux:select.option>
                        @endforeach
                    </flux:select>
                    <flux:select id="filter-ministro" placeholder="Ministro" size="sm">
                        <flux:select.option value="">Todos</flux:select.option>
                        @foreach($filters['ministros'] ?? [] as $m)
                            <flux:select.option value="{{ $m }}">{{ $m }}</flux:select.option>
                        @endforeach
                    </flux:select>
                    <flux:select id="filter-orgao" placeholder="Orgao Julgador" size="sm">
                        <flux:select.option value="">Todos</flux:select.option>
                        @foreach($filters['orgaos_julgadores'] ?? [] as $o)
                            <flux:select.option value="{{ $o }}">{{ $o }}</flux:select.option>
                        @endforeach
                    </flux:select>
                    <div>
                        <flux:label size="sm">Data de</flux:label>
                        <flux:input type="date" id="filter-data-from" size="sm" />
                    </div>
                    <div>
                        <flux:label size="sm">Data ate</flux:label>
                        <flux:input type="date" id="filter-data-to" size="sm" />
                    </div>
                </div>
            </aside>

            {{-- Conteudo principal --}}
            <div class="flex-1 min-w-0">
                <form id="search-form" class="mb-6">
                    <flux:input.group>
                        <flux:input
                            type="text"
                            id="query"
                            name="query"
                            placeholder="Ex: dano moral bancario, revisao contratual, responsabilidade civil objetiva..."
                            required
                            autofocus
                        />
                        <flux:button type="submit" id="btn-search" variant="primary">
                            Buscar
                        </flux:button>
                    </flux:input.group>
                </form>

                <div id="loading" class="hidden mt-8 text-center text-gray-500">
                    <div class="inline-block animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-navy-600"></div>
                    <span class="ml-2">Buscando...</span>
                </div>

                <div id="query-preprocessing" class="hidden mt-4 bg-navy-50 rounded-lg border border-navy-200 px-4 py-3 text-sm text-navy-700 space-y-1"></div>
                <div id="query-info" class="hidden mt-3 bg-white rounded-lg border border-gray-200 p-3 text-xs text-gray-500 flex gap-4 flex-wrap"></div>
                <div id="results" class="mt-4 space-y-0"></div>
            </div>
        </div>
    </div>

    {{-- Tab: Busca Decomposta --}}
    <div x-show="tab === 'decomposed'" x-cloak>
        <div class="max-w-4xl mx-auto">
            <p class="mb-4 text-sm text-gray-500">
                O agente decompoe sua query em sub-buscas por angulo juridico,
                explorando facetas distintas do tema. Resultados agrupados por perspectiva.
            </p>
            <livewire:decomposed-search />
        </div>
    </div>
</div>

<script>
// Busca direta (vanilla JS)
const form = document.getElementById('search-form');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const queryInfo = document.getElementById('query-info');
const queryPreprocessing = document.getElementById('query-preprocessing');
const btnSearch = document.getElementById('btn-search');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = document.getElementById('query').value.trim();
    if (!query || query.length < 3) return;

    const payload = { query };

    const filters = {};
    const tipo = document.getElementById('filter-tipo')?.value;
    const classe = document.getElementById('filter-classe')?.value;
    const ministro = document.getElementById('filter-ministro')?.value;
    const orgao = document.getElementById('filter-orgao')?.value;
    const dataFrom = document.getElementById('filter-data-from')?.value;
    const dataTo = document.getElementById('filter-data-to')?.value;

    if (tipo) filters.tipo = tipo;
    if (classe) filters.classe = classe;
    if (ministro) filters.ministro = ministro;
    if (orgao) filters.orgao_julgador = orgao;
    if (dataFrom) filters.data_from = dataFrom;
    if (dataTo) filters.data_to = dataTo;

    if (Object.keys(filters).length > 0) payload.filters = filters;

    loading.classList.remove('hidden');
    results.innerHTML = '';
    queryInfo.classList.add('hidden');
    queryPreprocessing.classList.add('hidden');
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
            results.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">${escapeHtml(data.error || 'Erro na busca')}</div>`;
            return;
        }

        if (data.query_info) {
            const preprocessingParts = [];

            if (data.query_info.processed_query && data.query_info.processed_query !== data.query_info.original_query) {
                preprocessingParts.push(`<span>Consulta processada: <strong>${escapeHtml(data.query_info.processed_query)}</strong></span>`);
            }

            if (data.query_info.extracted_filters) {
                const ef = data.query_info.extracted_filters;
                const filterLabels = [];
                if (ef.classe) filterLabels.push(`Classe ${ef.classe}`);
                if (ef.ministro) filterLabels.push(`Min. ${ef.ministro}`);
                if (ef.processo) filterLabels.push(`Processo ${ef.processo}`);
                if (ef.ano_from && ef.ano_to) {
                    const yearFrom = ef.ano_from.substring(0, 4);
                    const yearTo = ef.ano_to.substring(0, 4);
                    filterLabels.push(yearFrom === yearTo ? `Ano ${yearFrom}` : `Periodo ${yearFrom}-${yearTo}`);
                } else if (ef.ano_from) {
                    filterLabels.push(`A partir de ${ef.ano_from.substring(0, 4)}`);
                } else if (ef.ano_to) {
                    filterLabels.push(`Ate ${ef.ano_to.substring(0, 4)}`);
                }
                if (filterLabels.length > 0) {
                    preprocessingParts.push(`<span>Filtros detectados: <strong>${filterLabels.join(', ')}</strong></span>`);
                }
            }

            if (data.query_info.expanded_terms && data.query_info.expanded_terms.length > 0) {
                preprocessingParts.push(`<span>Termos expandidos: <strong>${data.query_info.expanded_terms.map(t => escapeHtml(t)).join(', ')}</strong></span>`);
            }

            if (preprocessingParts.length > 0) {
                queryPreprocessing.innerHTML = preprocessingParts.join('');
                queryPreprocessing.classList.remove('hidden');
            }

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

        results.innerHTML = data.results.map((item, i) => {
            const tipo = escapeHtml(item.tipo || '');
            const classe = escapeHtml(item.classe || '');
            const processo = escapeHtml(item.processo || '');
            const ministro = escapeHtml(item.ministro || '');
            const orgao = escapeHtml(item.orgao_julgador || '');
            const dataPub = escapeHtml(item.data_publicacao || '');
            const tipoClass = (item.tipo === 'ACORDAO' || item.tipo === 'ACÓRDÃO') ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700';

            const docUrl = item.doc_id ? `/document/${encodeURIComponent(item.doc_id)}` : '#';

            return `
            <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-5 hover:shadow-md transition ${i > 0 ? 'mt-3' : ''}">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex gap-2 text-xs flex-wrap">
                        ${tipo ? `<span class="px-2 py-0.5 rounded font-medium ${tipoClass}">${tipo}</span>` : ''}
                        ${classe ? `<span class="bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-medium">${classe}</span>` : ''}
                        <a href="${docUrl}" class="text-navy-700 font-medium hover:text-navy-500 hover:underline">${processo}</a>
                    </div>
                    <span class="text-xs font-mono ${item.scores.rrf >= 0.025 ? 'text-green-600' : item.scores.rrf >= 0.015 ? 'text-yellow-600' : 'text-gray-400'} whitespace-nowrap ml-2">#${i + 1} <span class="opacity-60">${item.scores.rrf.toFixed(4)}</span></span>
                </div>
                <p class="text-sm text-gray-700 leading-relaxed mb-3">${highlightTerms(item.content, query)}</p>
                <div class="flex justify-between items-center text-xs text-gray-400">
                    <div class="flex gap-3">
                        <span>${ministro}</span>
                        <span>${orgao}</span>
                        <span>${dataPub}</span>
                    </div>
                    <div class="flex gap-2 font-mono">
                        <span>d:${item.scores.dense.toFixed(3)}</span>
                        <span>s:${item.scores.sparse.toFixed(1)}</span>
                        <a href="${docUrl}" class="text-navy-500 hover:text-navy-700 hover:underline ml-2">Ver inteiro teor</a>
                    </div>
                </div>
            </div>`;
        }).join('');

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

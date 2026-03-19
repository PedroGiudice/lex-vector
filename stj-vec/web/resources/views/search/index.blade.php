@extends('layouts.app')

@section('title', 'Busca - STJ-Vec')

@section('content')
<div x-data="{ tab: 'direct' }">
    {{-- Tabs --}}
    <div class="flex gap-1 border-b border-slate-200 mb-6">
        <button
            @click="tab = 'direct'"
            :class="tab === 'direct' ? 'border-navy-700 text-navy-900 font-semibold' : 'border-transparent text-navy-400 hover:text-navy-600'"
            class="px-5 py-2.5 text-sm border-b-2 transition-colors"
        >
            Busca Direta
        </button>
        <button
            @click="tab = 'decomposed'"
            :class="tab === 'decomposed' ? 'border-navy-700 text-navy-900 font-semibold' : 'border-transparent text-navy-400 hover:text-navy-600'"
            class="px-5 py-2.5 text-sm border-b-2 transition-colors"
        >
            Busca Decomposta
        </button>
    </div>

    {{-- Tab: Busca Direta --}}
    <div x-show="tab === 'direct'" x-cloak>
        <div class="flex gap-6">
            {{-- Sidebar de filtros --}}
            <aside class="hidden lg:block w-60 flex-shrink-0">
                <div class="rounded-lg border border-slate-200 bg-white p-4 sticky top-6 space-y-4">
                    <h3 class="text-xs font-semibold text-navy-600 uppercase tracking-wider">Filtros</h3>
                    <div class="space-y-3">
                        @foreach([
                            ['filter-tipo', 'Tipo', 'Todos', $filters['tipos'] ?? []],
                            ['filter-classe', 'Classe', 'Todas', $filters['classes'] ?? []],
                            ['filter-ministro', 'Ministro', 'Todos', $filters['ministros'] ?? []],
                            ['filter-orgao', 'Orgao Julgador', 'Todos', $filters['orgaos_julgadores'] ?? []],
                        ] as [$id, $label, $default, $options])
                            <div>
                                <label for="{{ $id }}" class="block text-xs text-navy-400 mb-1">{{ $label }}</label>
                                <select id="{{ $id }}" class="w-full px-2.5 py-1.5 border border-slate-200 rounded-md text-sm bg-white text-navy-800 focus:ring-1 focus:ring-navy-300 focus:border-navy-300 transition-colors">
                                    <option value="">{{ $default }}</option>
                                    @foreach($options as $opt)
                                        <option value="{{ $opt }}">{{ $opt }}</option>
                                    @endforeach
                                </select>
                            </div>
                        @endforeach
                        <div>
                            <label for="filter-data-from" class="block text-xs text-navy-400 mb-1">Data de</label>
                            <input type="date" id="filter-data-from" class="w-full px-2.5 py-1.5 border border-slate-200 rounded-md text-sm bg-white text-navy-800 focus:ring-1 focus:ring-navy-300 focus:border-navy-300">
                        </div>
                        <div>
                            <label for="filter-data-to" class="block text-xs text-navy-400 mb-1">Data ate</label>
                            <input type="date" id="filter-data-to" class="w-full px-2.5 py-1.5 border border-slate-200 rounded-md text-sm bg-white text-navy-800 focus:ring-1 focus:ring-navy-300 focus:border-navy-300">
                        </div>
                    </div>
                </div>
            </aside>

            {{-- Conteudo principal --}}
            <div class="flex-1 min-w-0">
                <form id="search-form" class="mb-6">
                    <div class="flex gap-2">
                        <input
                            type="text"
                            id="query"
                            name="query"
                            placeholder="Ex: dano moral bancario, revisao contratual, responsabilidade civil objetiva..."
                            class="flex-1 px-4 py-2.5 border border-navy-200 rounded-lg focus:ring-2 focus:ring-navy-400/40 focus:border-navy-400 text-navy-900 placeholder-navy-300 bg-white transition-colors"
                            required
                            minlength="3"
                            autofocus
                        >
                        <button
                            type="submit"
                            id="btn-search"
                            class="px-6 py-2.5 bg-slate-800 text-white rounded-lg hover:bg-slate-700 active:bg-slate-900 transition-colors font-medium text-sm"
                        >
                            Buscar
                        </button>
                    </div>
                </form>

                <div id="loading" class="hidden mt-8 text-center text-navy-400">
                    <div class="inline-block animate-spin rounded-full h-5 w-5 border-2 border-navy-200 border-t-navy-600"></div>
                    <span class="ml-2 text-sm">Buscando...</span>
                </div>

                <div id="query-preprocessing" class="hidden mt-4 bg-navy-50 rounded-lg border border-slate-200 px-4 py-3 text-sm text-navy-700 space-y-1"></div>
                <div id="query-info" class="hidden mt-3 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-xs font-mono text-navy-400 flex gap-4 flex-wrap"></div>
                <div id="results" class="mt-4 space-y-0"></div>
            </div>
        </div>
    </div>

    {{-- Tab: Busca Decomposta --}}
    <div x-show="tab === 'decomposed'" x-cloak>
        <div class="max-w-4xl mx-auto">
            <p class="mb-4 text-sm text-navy-400">
                O agente decompoe sua query em sub-buscas por angulo juridico,
                explorando facetas distintas do tema. Resultados agrupados por perspectiva.
            </p>
            <livewire:decomposed-search />
        </div>
    </div>
</div>

<script>
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
            results.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">${escapeHtml(data.error || 'Erro na busca')}</div>`;
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
                <span>Total: <strong>${data.query_info.total_ms}ms</strong></span>
                <span>Dense: ${data.query_info.dense_candidates}</span>
                <span>Sparse: ${data.query_info.sparse_candidates}</span>
                <span>Resultados: ${data.query_info.post_filter_count}/${data.query_info.pre_filter_count}</span>
            `;
            queryInfo.classList.remove('hidden');
        }

        if (!data.results || data.results.length === 0) {
            results.innerHTML = '<div class="text-center text-navy-400 py-8 text-sm">Nenhum resultado encontrado.</div>';
            return;
        }

        results.innerHTML = data.results.map((item, i) => {
            const tipo = escapeHtml(item.tipo || '');
            const classe = escapeHtml(item.classe || '');
            const processo = escapeHtml(item.processo || '');
            const ministro = escapeHtml(item.ministro || '');
            const orgao = escapeHtml(item.orgao_julgador || '');
            const dataPub = escapeHtml(item.data_publicacao || '');
            const tipoClass = (item.tipo === 'ACORDAO' || item.tipo === 'AC\u00d3RD\u00c3O') ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700';
            const rrf = item.scores.rrf;
            const rrfColor = rrf >= 0.025 ? '#16a34a' : rrf >= 0.015 ? '#d97706' : '#9fb3c8';
            const rrfPct = Math.min(rrf / 0.035 * 100, 100);

            const docUrl = item.doc_id ? `/document/${encodeURIComponent(item.doc_id)}` : '#';

            return `
            <div class="result-card bg-white rounded-lg border border-slate-200 p-4 ${i > 0 ? 'mt-2.5' : ''}">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex gap-1.5 items-center flex-wrap">
                        ${tipo ? `<span class="px-2 py-0.5 rounded text-xs font-medium ${tipoClass}">${tipo}</span>` : ''}
                        ${classe ? `<span class="bg-navy-50 text-navy-600 px-2 py-0.5 rounded text-xs font-medium">${classe}</span>` : ''}
                        <a href="${docUrl}" class="text-sm text-navy-800 font-medium hover:text-navy-600 hover:underline transition-colors">${processo}</a>
                    </div>
                    <div class="flex items-center gap-2 ml-3 shrink-0">
                        <div class="relevance-bar" style="width:36px"><div class="relevance-bar-fill" style="width:${rrfPct}%;background:${rrfColor}"></div></div>
                        <span class="text-xs font-mono" style="color:${rrfColor}">${rrf.toFixed(4)}</span>
                    </div>
                </div>
                <p class="text-sm text-navy-700 leading-relaxed mb-2.5">${highlightTerms(item.content, query)}</p>
                <div class="flex justify-between items-center text-xs text-navy-300">
                    <div class="flex gap-3">
                        ${ministro ? `<span>${ministro}</span>` : ''}
                        ${orgao ? `<span>${orgao}</span>` : ''}
                        ${dataPub ? `<span>${dataPub}</span>` : ''}
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="font-mono text-navy-300/70">d:${item.scores.dense.toFixed(3)} s:${item.scores.sparse.toFixed(1)}</span>
                        <a href="${docUrl}" class="text-navy-500 hover:text-navy-700 hover:underline transition-colors font-medium">Ver inteiro teor</a>
                    </div>
                </div>
            </div>`;
        }).join('');

    } catch (err) {
        results.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">Erro de conexao: ${err.message}</div>`;
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
    return escaped.replace(regex, '<mark class="search-highlight">$1</mark>');
}
</script>
@endsection

<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class SearchController extends Controller
{
    private string $rustBaseUrl;

    public function __construct()
    {
        $this->rustBaseUrl = config('services.stj_search.url', 'http://localhost:8421');
    }

    public function index(): \Illuminate\View\View
    {
        $filters = cache()->remember('stj_filters', 3600, function () {
            $response = Http::timeout(5)->get("{$this->rustBaseUrl}/api/filters");

            return $response->successful() ? $response->json() : [];
        });

        return view('search.index', compact('filters'));
    }

    public function search(Request $request): \Illuminate\Http\JsonResponse
    {
        $validated = $request->validate([
            'query' => 'required|string|min:3|max:500',
            'limit' => 'nullable|integer|min:1|max:100',
            'filters.ministro' => 'nullable|string',
            'filters.tipo' => 'nullable|string',
            'filters.classe' => 'nullable|string',
            'filters.orgao_julgador' => 'nullable|string',
            'filters.data_from' => 'nullable|date_format:Y-m-d',
            'filters.data_to' => 'nullable|date_format:Y-m-d',
        ]);

        $payload = ['query' => $validated['query']];

        if (isset($validated['limit'])) {
            $payload['limit'] = $validated['limit'];
        }

        $filters = array_filter($validated['filters'] ?? []);
        if (! empty($filters)) {
            $payload['filters'] = $filters;
        }

        $response = Http::timeout(30)->post("{$this->rustBaseUrl}/api/search", $payload);

        if (! $response->successful()) {
            return response()->json([
                'error' => 'Erro na busca',
                'detail' => $response->body(),
            ], $response->status());
        }

        return response()->json($response->json());
    }

    public function document(string $docId): \Illuminate\Http\JsonResponse
    {
        $response = Http::timeout(10)->get("{$this->rustBaseUrl}/api/document/{$docId}");

        if (! $response->successful()) {
            return response()->json([
                'error' => 'Documento nao encontrado',
            ], $response->status());
        }

        return response()->json($response->json());
    }
}

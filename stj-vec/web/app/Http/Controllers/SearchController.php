<?php

namespace App\Http\Controllers;

use App\Http\Requests\SearchRequest;
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

    public function search(SearchRequest $request): \Illuminate\Http\JsonResponse
    {
        $payload = $request->toPayload();

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

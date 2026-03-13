<?php

namespace Tests\Feature;

use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class SearchControllerTest extends TestCase
{
    public function test_index_returns_200(): void
    {
        Http::fake([
            '*/api/filters' => Http::response([
                'tipos' => ['ACORDAO', 'DECISAO'],
                'classes' => ['REsp', 'HC'],
                'ministros' => ['Min. Test'],
                'orgaos_julgadores' => ['PRIMEIRA TURMA'],
            ]),
        ]);

        $response = $this->get('/');

        $response->assertStatus(200);
        $response->assertSee('Busca Direta');
        $response->assertSee('Busca Decomposta');
    }

    public function test_index_renders_filters(): void
    {
        Http::fake([
            '*/api/filters' => Http::response([
                'tipos' => ['ACORDAO'],
                'classes' => ['REsp'],
                'ministros' => [],
                'orgaos_julgadores' => [],
            ]),
        ]);

        $response = $this->get('/');

        $response->assertSee('ACORDAO');
        $response->assertSee('REsp');
    }

    public function test_search_validates_query_required(): void
    {
        $response = $this->postJson('/search', []);

        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['query']);
    }

    public function test_search_validates_query_min_length(): void
    {
        $response = $this->postJson('/search', ['query' => 'ab']);

        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['query']);
    }

    public function test_search_forwards_to_rust_backend(): void
    {
        Http::fake([
            '*/api/search' => Http::response([
                'results' => [
                    ['doc_id' => '123', 'processo' => 'REsp 1.234/SP'],
                ],
                'query_info' => ['total_ms' => 150],
            ]),
        ]);

        $response = $this->postJson('/search', ['query' => 'dano moral banco']);

        $response->assertStatus(200);
        $response->assertJsonPath('results.0.doc_id', '123');
    }

    public function test_search_forwards_filters(): void
    {
        Http::fake([
            '*/api/search' => Http::response(['results' => []]),
        ]);

        $this->postJson('/search', [
            'query' => 'dano moral',
            'filters' => ['tipo' => 'ACORDAO', 'classe' => 'REsp'],
        ]);

        Http::assertSent(function ($request) {
            $body = $request->data();

            return $body['query'] === 'dano moral'
                && $body['filters']['tipo'] === 'ACORDAO'
                && $body['filters']['classe'] === 'REsp';
        });
    }

    public function test_search_returns_error_on_backend_failure(): void
    {
        Http::fake([
            '*/api/search' => Http::response('Internal Server Error', 500),
        ]);

        $response = $this->postJson('/search', ['query' => 'dano moral banco']);

        $response->assertStatus(500);
        $response->assertJsonPath('error', 'Erro na busca');
    }

    public function test_document_returns_json(): void
    {
        Http::fake([
            '*/api/document/doc-123' => Http::response([
                'doc_id' => 'doc-123',
                'content' => 'Full document text',
            ]),
        ]);

        $response = $this->getJson('/document/doc-123');

        $response->assertStatus(200);
        $response->assertJsonPath('doc_id', 'doc-123');
    }

    public function test_document_returns_404_on_not_found(): void
    {
        Http::fake([
            '*/api/document/missing' => Http::response('Not Found', 404),
        ]);

        $response = $this->getJson('/document/missing');

        $response->assertStatus(404);
        $response->assertJsonPath('error', 'Documento nao encontrado');
    }
}

<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class SearchStreamControllerTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('local');
        $this->actingAs(User::factory()->create(['must_change_password' => false]));
    }

    public function test_stream_returns_404_for_unknown_search(): void
    {
        $response = $this->get('/api/search/nonexistent-id/stream');

        $response->assertStatus(404);
    }

    public function test_stream_returns_sse_content_type(): void
    {
        Storage::disk('local')->put('searches/test-id.meta.json', json_encode([
            'pid' => 99999,
            'query' => 'dano moral',
            'started_at' => time(),
        ]));

        Storage::disk('local')->put('searches/test-id.result.json', json_encode([
            'results' => [['doc_id' => 'x']],
            'decomposition' => ['angles' => []],
        ]));

        $response = $this->get('/api/search/test-id/stream');

        $response->assertStatus(200);
        $response->assertHeader('Content-Type', 'text/event-stream; charset=UTF-8');
        $response->assertHeader('Cache-Control', 'no-cache, private');
        $response->assertHeader('X-Accel-Buffering', 'no');
    }

    public function test_stream_emits_completed_when_result_exists(): void
    {
        Storage::disk('local')->put('searches/test-id.meta.json', json_encode([
            'pid' => 99999,
            'query' => 'dano moral',
            'started_at' => time(),
        ]));

        Storage::disk('local')->put('searches/test-id.result.json', json_encode([
            'results' => [['doc_id' => 'x']],
            'decomposition' => ['angles' => []],
        ]));

        $response = $this->get('/api/search/test-id/stream');
        $content = $response->streamedContent();

        $this->assertStringContainsString('event: completed', $content);
    }

    public function test_stream_emits_stderr_events(): void
    {
        Storage::disk('local')->put('searches/test-id.meta.json', json_encode([
            'pid' => 99999,
            'query' => 'dano moral',
            'started_at' => time(),
        ]));

        $stderrPath = Storage::disk('local')->path('searches/test-id.stderr.log');
        file_put_contents($stderrPath, json_encode(['event' => 'search_started', 'angle' => 'dano moral', 'timestamp' => time()])."\n");

        Storage::disk('local')->put('searches/test-id.result.json', json_encode([
            'results' => [['doc_id' => 'x']],
            'decomposition' => ['angles' => []],
        ]));

        $response = $this->get('/api/search/test-id/stream');
        $content = $response->streamedContent();

        $this->assertStringContainsString('event: search_started', $content);
        $this->assertStringContainsString('dano moral', $content);
    }
}

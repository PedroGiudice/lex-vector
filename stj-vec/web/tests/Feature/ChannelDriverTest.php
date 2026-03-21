<?php

namespace Tests\Feature;

use App\Livewire\DecomposedSearch;
use App\Services\AgentRunnerInterface;
use App\Services\ChannelSessionManager;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Livewire\Livewire;
use Mockery;
use Tests\TestCase;

class ChannelDriverTest extends TestCase
{
    use RefreshDatabase;

    private function mockChannelManager(bool $alive = true): ChannelSessionManager&\Mockery\MockInterface
    {
        $mock = Mockery::mock(ChannelSessionManager::class);
        $mock->shouldReceive('ensureRunning')->andReturn($alive);
        $mock->shouldReceive('sendQuery')->andReturnUsing(fn ($q, $id) => $id);
        $mock->shouldReceive('streamUrl')->andReturnUsing(fn ($id) => "http://127.0.0.1:8790/stream/{$id}");
        $mock->shouldReceive('isAlive')->andReturn($alive);

        $this->app->instance(ChannelSessionManager::class, $mock);

        return $mock;
    }

    private function mockRunner(): void
    {
        $mock = Mockery::mock(AgentRunnerInterface::class);
        $mock->shouldReceive('start')->andReturnNull();
        $mock->shouldReceive('isComplete')->andReturn(false);
        $mock->shouldReceive('getResult')->andReturnNull();
        $mock->shouldReceive('cancel')->andReturnNull();
        $mock->shouldReceive('isProcessDead')->andReturn(false);

        $this->app->instance(AgentRunnerInterface::class, $mock);
    }

    public function test_channel_driver_creates_search_job(): void
    {
        $this->mockChannelManager();

        Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'inaplicabilidade CDC software')
            ->call('startSearch');

        $this->assertDatabaseHas('search_jobs', [
            'query' => 'inaplicabilidade CDC software',
            'driver' => 'channel',
            'status' => 'running',
        ]);
    }

    public function test_channel_driver_sets_channel_stream_url(): void
    {
        $this->mockChannelManager();

        $component = Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'dano moral bancario')
            ->call('startSearch');

        $streamUrl = $component->get('channelStreamUrl');
        $this->assertNotNull($streamUrl);
        $this->assertStringContainsString('http://127.0.0.1:8790/stream/', $streamUrl);
    }

    public function test_channel_driver_sets_status_searching(): void
    {
        $this->mockChannelManager();

        Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'responsabilidade civil objetiva')
            ->call('startSearch')
            ->assertSet('status', 'searching');
    }

    public function test_channel_driver_does_not_set_regular_stream_url(): void
    {
        $this->mockChannelManager();

        $component = Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'teoria finalista mitigada')
            ->call('startSearch');

        $this->assertNull($component->get('streamUrl'));
    }

    public function test_channel_driver_calls_send_query(): void
    {
        $mock = Mockery::mock(ChannelSessionManager::class);
        $mock->shouldReceive('ensureRunning')->andReturn(true);
        $mock->shouldReceive('isAlive')->andReturn(true);
        $mock->shouldReceive('sendQuery')
            ->once()
            ->withArgs(fn ($query, $requestId) => $query === 'prescricao intercorrente' && is_string($requestId))
            ->andReturnUsing(fn ($q, $id) => $id);
        $mock->shouldReceive('streamUrl')->andReturnUsing(fn ($id) => "http://127.0.0.1:8790/stream/{$id}");

        $this->app->instance(ChannelSessionManager::class, $mock);

        Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'prescricao intercorrente')
            ->call('startSearch');
    }

    public function test_channel_driver_handles_connection_error(): void
    {
        $mock = Mockery::mock(ChannelSessionManager::class);
        $mock->shouldReceive('ensureRunning')->andReturn(true);
        $mock->shouldReceive('sendQuery')->andThrow(new \RuntimeException('Connection refused'));
        $mock->shouldReceive('streamUrl')->andReturn('http://127.0.0.1:8790/stream/test');

        $this->app->instance(ChannelSessionManager::class, $mock);

        Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'dano moral bancario')
            ->call('startSearch')
            ->assertSet('status', 'error')
            ->assertSee('Falha ao conectar ao pesquisador');
    }

    public function test_persist_analysis_updates_search_job(): void
    {
        $this->mockChannelManager();

        $component = Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'vulnerabilidade consumidor')
            ->call('startSearch');

        $searchId = $component->get('searchId');
        $analysisText = 'A jurisprudencia do STJ consagra a teoria finalista mitigada (REsp 1.234.567/SP).';

        $component->call('persistAnalysis', $analysisText)
            ->assertSet('status', 'completed')
            ->assertSet('analysis', $analysisText);

        $this->assertDatabaseHas('search_jobs', [
            'id' => $searchId,
            'status' => 'completed',
            'analysis' => $analysisText,
        ]);
    }

    public function test_persist_analysis_renders_markdown(): void
    {
        $this->mockChannelManager();

        Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'dano moral bancario')
            ->call('startSearch')
            ->call('persistAnalysis', '**Tese predominante:** responsabilidade objetiva.')
            ->assertSee('Tese predominante:')
            ->assertSee('responsabilidade objetiva.');
    }

    public function test_cancel_resets_channel_state(): void
    {
        $this->mockChannelManager();

        Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'dano moral bancario')
            ->call('startSearch')
            ->call('cancelSearch')
            ->assertSet('status', 'idle')
            ->assertSet('channelStreamUrl', null)
            ->assertSet('analysis', null)
            ->assertSet('searchId', null);
    }

    public function test_load_history_job_loads_analysis(): void
    {
        Livewire::test(DecomposedSearch::class)
            ->call('loadHistoryJob', [
                'query' => 'teoria finalista mitigada',
                'results' => [],
                'decomposition' => null,
                'analysis' => 'Analise juridica completa sobre a teoria finalista mitigada.',
                'duration_ms' => 45000,
            ])
            ->assertSet('analysis', 'Analise juridica completa sobre a teoria finalista mitigada.')
            ->assertSet('status', 'completed')
            ->assertSet('channelStreamUrl', null);
    }

    public function test_channel_driver_validation_rejects_short_query(): void
    {
        $this->mockChannelManager();

        Livewire::test(DecomposedSearch::class)
            ->set('driver', 'channel')
            ->set('query', 'ab')
            ->call('startSearch')
            ->assertHasErrors(['query']);

        $this->assertDatabaseMissing('search_jobs', [
            'driver' => 'channel',
        ]);
    }

    public function test_cli_driver_does_not_use_channel_manager(): void
    {
        $this->mockRunner();

        $component = Livewire::test(DecomposedSearch::class)
            ->set('driver', 'cli')
            ->set('query', 'dano moral bancario')
            ->call('startSearch');

        $this->assertNull($component->get('channelStreamUrl'));
        $this->assertNotNull($component->get('streamUrl'));
    }

    public function test_channel_driver_renders_radio_option(): void
    {
        Livewire::test(DecomposedSearch::class)
            ->assertSee('Pesquisador');
    }
}

<?php

namespace Tests\Feature;

use App\Livewire\DecomposedSearch;
use App\Services\AgentRunnerInterface;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Livewire\Livewire;
use Mockery;
use Tests\TestCase;

class DecomposedSearchTest extends TestCase
{
    use RefreshDatabase;

    private function mockRunner(bool $complete = false, ?array $result = null): void
    {
        $mock = Mockery::mock(AgentRunnerInterface::class);
        $mock->shouldReceive('start')->andReturnNull();
        $mock->shouldReceive('isComplete')->andReturn($complete);
        $mock->shouldReceive('getResult')->andReturn($result);
        $mock->shouldReceive('cancel')->andReturnNull();
        $mock->shouldReceive('isProcessDead')->andReturn(false);

        $this->app->instance(AgentRunnerInterface::class, $mock);
    }

    public function test_can_render_component(): void
    {
        Livewire::test(DecomposedSearch::class)
            ->assertStatus(200)
            ->assertSee('Decompor e Buscar');
    }

    public function test_start_search_changes_status(): void
    {
        $this->mockRunner();

        $component = Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->assertSet('status', 'searching');

        $this->assertNotNull($component->get('searchId'));
    }

    public function test_validation_rejects_short_query(): void
    {
        Livewire::test(DecomposedSearch::class)
            ->set('query', 'ab')
            ->call('startSearch')
            ->assertHasErrors(['query']);
    }

    public function test_poll_returns_results_when_complete(): void
    {
        $fixture = json_decode(
            file_get_contents(base_path('tests/fixtures/sdk-output-sample.json')),
            true
        );

        $this->mockRunner(complete: true, result: $fixture);

        $component = Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('checkResult')
            ->assertSet('status', 'completed');

        $this->assertNotNull($component->get('results'));
        $this->assertNotNull($component->get('decomposition'));
    }

    public function test_poll_keeps_searching_when_not_complete(): void
    {
        $this->mockRunner(complete: false);

        Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('checkResult')
            ->assertSet('status', 'searching');
    }

    public function test_cancel_resets_state(): void
    {
        $this->mockRunner();

        Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('cancelSearch')
            ->assertSet('status', 'idle')
            ->assertSet('searchId', null);
    }

    public function test_completed_shows_angle_chips(): void
    {
        $fixture = json_decode(
            file_get_contents(base_path('tests/fixtures/sdk-output-sample.json')),
            true
        );

        $this->mockRunner(complete: true, result: $fixture);

        Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('checkResult')
            ->assertSee('Inscricao indevida em cadastros restritivos')
            ->assertSee('Responsabilidade objetiva do banco')
            ->assertSee('Aplicabilidade do CDC');
    }

    public function test_completed_shows_result_cards(): void
    {
        $fixture = json_decode(
            file_get_contents(base_path('tests/fixtures/sdk-output-sample.json')),
            true
        );

        $this->mockRunner(complete: true, result: $fixture);

        Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('checkResult')
            ->assertSee('REsp 1.234.567/SP')
            ->assertSee('Min. Nancy Andrighi')
            ->assertSee('TERCEIRA TURMA');
    }

    public function test_load_result_sets_completed(): void
    {
        $fixture = json_decode(
            file_get_contents(base_path('tests/fixtures/sdk-output-sample.json')),
            true
        );

        $this->mockRunner(complete: true, result: $fixture);

        $component = Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('loadResult')
            ->assertSet('status', 'completed');

        $this->assertNotNull($component->get('results'));
    }

    public function test_mark_error_sets_error(): void
    {
        $this->mockRunner();

        Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('markError')
            ->assertSet('status', 'error');
    }

    public function test_mark_timeout_sets_timeout(): void
    {
        $this->mockRunner();

        Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch')
            ->call('markTimeout')
            ->assertSet('status', 'timeout');
    }

    public function test_stream_url_null_when_idle(): void
    {
        Livewire::test(DecomposedSearch::class)
            ->assertSet('streamUrl', null);
    }

    public function test_stream_url_set_when_searching(): void
    {
        $this->mockRunner();

        $component = Livewire::test(DecomposedSearch::class)
            ->set('query', 'dano moral banco')
            ->call('startSearch');

        $streamUrl = $component->get('streamUrl');
        $this->assertNotNull($streamUrl);
        $this->assertStringContainsString('/api/search/', $streamUrl);
        $this->assertStringContainsString('/stream', $streamUrl);
    }
}

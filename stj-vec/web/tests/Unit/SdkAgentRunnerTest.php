<?php

namespace Tests\Unit;

use App\Services\SdkAgentRunner;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class SdkAgentRunnerTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('local');
    }

    public function test_start_creates_meta_file(): void
    {
        config([
            'services.agent.bun_bin' => '/usr/bin/echo',
            'services.agent.sdk_script' => '/tmp/fake-decompose.ts',
        ]);

        $runner = new SdkAgentRunner;
        $runner->start('test-uuid-123', 'dano moral banco');

        Storage::disk('local')->assertExists('searches/test-uuid-123.meta.json');

        $meta = json_decode(Storage::disk('local')->get('searches/test-uuid-123.meta.json'), true);
        $this->assertEquals('dano moral banco', $meta['query']);
        $this->assertArrayHasKey('started_at', $meta);
        $this->assertArrayHasKey('pid', $meta);
    }

    public function test_is_complete_returns_false_when_no_result(): void
    {
        $runner = new SdkAgentRunner;
        $this->assertFalse($runner->isComplete('nonexistent-uuid'));
    }

    public function test_is_complete_returns_false_for_empty_file(): void
    {
        Storage::disk('local')->put('searches/short.result.json', '{}');

        $runner = new SdkAgentRunner;
        $this->assertFalse($runner->isComplete('short'));
    }

    public function test_is_complete_returns_true_for_valid_result(): void
    {
        $fixture = file_get_contents(base_path('tests/fixtures/sdk-output-sample.json'));
        Storage::disk('local')->put('searches/valid-uuid.result.json', $fixture);

        $runner = new SdkAgentRunner;
        $this->assertTrue($runner->isComplete('valid-uuid'));
    }

    public function test_get_result_parses_json(): void
    {
        $fixture = file_get_contents(base_path('tests/fixtures/sdk-output-sample.json'));
        Storage::disk('local')->put('searches/parsed-uuid.result.json', $fixture);

        $runner = new SdkAgentRunner;
        $result = $runner->getResult('parsed-uuid');

        $this->assertNotNull($result);
        $this->assertEquals('dano moral negativacao indevida banco', $result['original_query']);
        $this->assertCount(6, $result['decomposition']['angles']);
        $this->assertCount(5, $result['results']);
        $this->assertEquals(40, $result['total_results']);
    }

    public function test_get_result_returns_null_for_invalid_json(): void
    {
        Storage::disk('local')->put('searches/bad-json.result.json', 'this is not json at all');

        $runner = new SdkAgentRunner;
        $this->assertNull($runner->getResult('bad-json'));
    }

    public function test_get_result_returns_null_when_not_complete(): void
    {
        $runner = new SdkAgentRunner;
        $this->assertNull($runner->getResult('missing-uuid'));
    }

    public function test_cleanup_returns_zero_when_no_old_files(): void
    {
        Storage::disk('local')->put('searches/recent.meta.json', '{}');

        $runner = new SdkAgentRunner;
        $removed = $runner->cleanup(24);

        $this->assertEquals(0, $removed);
        Storage::disk('local')->assertExists('searches/recent.meta.json');
    }

    public function test_cleanup_removes_files_with_zero_max_age(): void
    {
        Storage::disk('local')->put('searches/any.meta.json', '{}');
        Storage::disk('local')->put('searches/any.result.json', '{"data":true}');

        sleep(1);

        $runner = new SdkAgentRunner;
        $removed = $runner->cleanup(0);

        $this->assertGreaterThanOrEqual(2, $removed);
    }

    public function test_cancel_deletes_files(): void
    {
        Storage::disk('local')->put('searches/cancel-me.meta.json', json_encode([
            'pid' => '99999',
            'query' => 'test',
            'started_at' => time(),
        ]));
        Storage::disk('local')->put('searches/cancel-me.result.json', '{"test": true}');

        $runner = new SdkAgentRunner;
        $runner->cancel('cancel-me');

        Storage::disk('local')->assertMissing('searches/cancel-me.meta.json');
        Storage::disk('local')->assertMissing('searches/cancel-me.result.json');
    }

    public function test_driver_config_resolves_sdk_runner(): void
    {
        config(['services.agent.driver' => 'sdk']);

        $resolved = app(\App\Services\AgentRunnerInterface::class);
        $this->assertInstanceOf(SdkAgentRunner::class, $resolved);
    }

    public function test_driver_config_resolves_cli_runner(): void
    {
        config(['services.agent.driver' => 'cli']);

        $resolved = app(\App\Services\AgentRunnerInterface::class);
        $this->assertInstanceOf(\App\Services\AgentRunner::class, $resolved);
    }
}

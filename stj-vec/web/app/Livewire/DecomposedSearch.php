<?php

namespace App\Livewire;

use App\Models\SearchJob;
use App\Services\AgentRunnerInterface;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Livewire\Attributes\Validate;
use Livewire\Component;

class DecomposedSearch extends Component
{
    #[Validate('required|string|min:3|max:500')]
    public string $query = '';

    public string $driver = 'cli';

    public ?string $searchId = null;

    public string $status = 'idle';

    /** @var array<string, mixed>|null */
    public ?array $results = null;

    /** @var array<string, mixed>|null */
    public ?array $decomposition = null;

    public ?string $errorMessage = null;

    public ?string $streamUrl = null;

    public ?int $startedAt = null;

    public int $elapsedSeconds = 0;

    private const TIMEOUT_SECONDS = 600;

    public function startSearch(): void
    {
        $this->validate();

        $this->searchId = Str::uuid()->toString();
        $this->status = 'searching';
        $this->startedAt = time();
        $this->elapsedSeconds = 0;
        $this->results = null;
        $this->decomposition = null;
        $this->errorMessage = null;
        $this->streamUrl = null;

        $this->runner()->start($this->searchId, $this->query);

        SearchJob::create([
            'id' => $this->searchId,
            'query' => $this->query,
            'driver' => $this->driver,
            'status' => 'running',
        ]);

        $this->streamUrl = route('search.stream', $this->searchId);
    }

    public function checkResult(): void
    {
        if ($this->status !== 'searching' || $this->searchId === null) {
            return;
        }

        $this->elapsedSeconds = time() - $this->startedAt;

        if ($this->elapsedSeconds > self::TIMEOUT_SECONDS) {
            $this->status = 'timeout';

            return;
        }

        $runner = $this->runner();
        $result = $runner->getResult($this->searchId);

        if ($result !== null) {
            if (isset($result['narrative'])) {
                $this->results = [];
                $this->decomposition = ['narrative' => $result['narrative']];
            } else {
                $this->results = $result['results'] ?? [];
                $this->decomposition = $result['decomposition'] ?? null;
            }
            $this->status = 'completed';
            $this->persistJobResult($result);

            return;
        }

        // No result yet -- check if the process died without producing output
        if ($runner->isProcessDead($this->searchId)) {
            $this->status = 'error';
            $this->errorMessage = $this->extractErrorFromStderr();
            $this->persistJobError($this->errorMessage);
        }
    }

    public function loadResult(): void
    {
        if ($this->searchId === null) {
            return;
        }

        // Retry a few times -- stdout may flush slightly after stderr signals 'completed'
        $runner = $this->runner();
        for ($attempt = 0; $attempt < 5; $attempt++) {
            $result = $runner->getResult($this->searchId);
            if ($result !== null) {
                if (isset($result['narrative'])) {
                    // Agent returned narrative text instead of structured JSON
                    $this->results = [];
                    $this->decomposition = ['narrative' => $result['narrative']];
                } else {
                    $this->results = $result['results'] ?? [];
                    $this->decomposition = $result['decomposition'] ?? null;
                }
                $this->status = 'completed';
                $this->persistJobResult($result);

                return;
            }
            usleep(300_000);
        }

        $this->status = 'error';
        $this->errorMessage = $this->extractErrorFromStderr();
        $this->persistJobError($this->errorMessage);
    }

    public function markError(?string $message = null): void
    {
        $this->status = 'error';
        $this->errorMessage = $message;
    }

    public function markTimeout(): void
    {
        $this->status = 'timeout';
    }

    public function cancelSearch(): void
    {
        if ($this->searchId !== null) {
            $this->runner()->cancel($this->searchId);
        }

        $this->reset(['searchId', 'status', 'results', 'decomposition', 'startedAt', 'elapsedSeconds', 'errorMessage', 'streamUrl']);
    }

    private function extractErrorFromStderr(): ?string
    {
        if ($this->searchId === null) {
            return null;
        }

        // 1. Check stderr.log for NDJSON error events (SDK driver)
        $stderrPath = "searches/{$this->searchId}.stderr.log";
        if (Storage::disk('local')->exists($stderrPath)) {
            $content = Storage::disk('local')->get($stderrPath);
            $lines = array_filter(explode("\n", trim($content)));

            foreach (array_reverse($lines) as $line) {
                $decoded = json_decode($line, true);
                if (json_last_error() !== JSON_ERROR_NONE) {
                    continue;
                }

                $msg = $decoded['message'] ?? $decoded['error'] ?? null;
                if ($msg !== null) {
                    return $this->humanizeApiError((string) $msg);
                }
            }
        }

        // 2. Check result.json for CLI envelope with is_error (CLI driver)
        $resultPath = "searches/{$this->searchId}.result.json";
        if (Storage::disk('local')->exists($resultPath)) {
            $raw = Storage::disk('local')->get($resultPath);
            $decoded = json_decode($raw, true);
            if (json_last_error() === JSON_ERROR_NONE && ! empty($decoded['is_error'])) {
                $msg = $decoded['result'] ?? null;
                if ($msg !== null) {
                    return $this->humanizeApiError((string) $msg);
                }
            }
        }

        return null;
    }

    private function humanizeApiError(string $msg): string
    {
        if (str_contains($msg, 'usage limits')) {
            return 'Limite de uso da API Anthropic atingido. Verifique seus creditos.';
        }
        if (str_contains($msg, 'authentication') || str_contains($msg, 'api_key')) {
            return 'Erro de autenticacao com a API Anthropic. Verifique a API key.';
        }
        if (str_contains($msg, 'rate_limit')) {
            return 'Rate limit da API Anthropic. Tente novamente em alguns segundos.';
        }

        return Str::limit($msg, 200);
    }

    #[\Livewire\Attributes\On('load-history-job')]
    public function loadHistoryJob(array $data): void
    {
        $this->query = $data['query'] ?? '';
        $this->results = $data['results'] ?? [];
        $this->decomposition = $data['decomposition'] ?? null;
        $this->elapsedSeconds = (int) round(($data['duration_ms'] ?? 0) / 1000);
        $this->status = 'completed';
        $this->errorMessage = null;
        $this->streamUrl = null;
    }

    private function persistJobResult(array $result): void
    {
        SearchJob::where('id', $this->searchId)->update([
            'status' => 'completed',
            'decomposition' => $result['decomposition'] ?? null,
            'results' => $result['results'] ?? null,
            'total_results' => $result['total_results'] ?? count($result['results'] ?? []),
            'total_searches' => $result['total_searches'] ?? null,
            'duration_ms' => $this->startedAt ? (time() - $this->startedAt) * 1000 : null,
        ]);

        $this->dispatch('search-completed');
    }

    private function persistJobError(?string $message): void
    {
        SearchJob::where('id', $this->searchId)->update([
            'status' => 'error',
            'error_message' => $message,
            'duration_ms' => $this->startedAt ? (time() - $this->startedAt) * 1000 : null,
        ]);
    }

    private function runner(): AgentRunnerInterface
    {
        config(['services.agent.driver' => $this->driver]);

        return app(AgentRunnerInterface::class);
    }

    public function render(): \Illuminate\View\View
    {
        return view('livewire.decomposed-search');
    }
}

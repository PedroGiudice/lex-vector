<?php

namespace App\Livewire;

use App\Services\AgentRunnerInterface;
use Illuminate\Support\Str;
use Livewire\Attributes\Validate;
use Livewire\Component;

class DecomposedSearch extends Component
{
    #[Validate('required|string|min:3|max:500')]
    public string $query = '';

    public ?string $searchId = null;

    public string $status = 'idle';

    /** @var array<string, mixed>|null */
    public ?array $results = null;

    /** @var array<string, mixed>|null */
    public ?array $decomposition = null;

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

        $runner = app(AgentRunnerInterface::class);
        $runner->start($this->searchId, $this->query);
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

        $runner = app(AgentRunnerInterface::class);

        if (! $runner->isComplete($this->searchId)) {
            if ($runner->isProcessDead($this->searchId)) {
                $this->status = 'error';
            }

            return;
        }

        $result = $runner->getResult($this->searchId);

        if ($result === null) {
            $this->status = 'error';

            return;
        }

        $this->results = $result['results'] ?? [];
        $this->decomposition = $result['decomposition'] ?? null;
        $this->status = 'completed';
    }

    public function cancelSearch(): void
    {
        if ($this->searchId !== null) {
            $runner = app(AgentRunnerInterface::class);
            $runner->cancel($this->searchId);
        }

        $this->reset(['searchId', 'status', 'results', 'decomposition', 'startedAt', 'elapsedSeconds']);
    }

    public function render(): \Illuminate\View\View
    {
        return view('livewire.decomposed-search');
    }
}

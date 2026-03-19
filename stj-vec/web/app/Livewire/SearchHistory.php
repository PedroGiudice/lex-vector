<?php

namespace App\Livewire;

use App\Models\SearchJob;
use Livewire\Component;

class SearchHistory extends Component
{
    /** @var array<string, mixed>|null */
    public ?array $selectedJob = null;

    /**
     * @return array<string, mixed>
     */
    #[\Livewire\Attributes\On('search-completed')]
    public function refreshHistory(): void
    {
        // Re-render on new search completion
    }

    public function loadJob(string $id): void
    {
        $job = SearchJob::find($id);

        if (! $job || $job->status !== 'completed') {
            return;
        }

        $this->dispatch('load-history-job', [
            'query' => $job->query,
            'results' => $job->results,
            'decomposition' => $job->decomposition,
            'total_results' => $job->total_results,
            'duration_ms' => $job->duration_ms,
        ]);
    }

    public function render(): \Illuminate\View\View
    {
        $jobs = SearchJob::query()
            ->latest()
            ->limit(30)
            ->get(['id', 'query', 'status', 'driver', 'total_results', 'duration_ms', 'created_at']);

        return view('livewire.search-history', [
            'jobs' => $jobs,
        ]);
    }
}

<?php

namespace App\Services;

use Illuminate\Support\Facades\Process;
use Illuminate\Support\Facades\Storage;

class AgentRunner implements AgentRunnerInterface
{
    private string $claudeBin;

    private string $agentPath;

    private string $model;

    public function __construct()
    {
        $this->claudeBin = config('services.agent.claude_bin');
        $this->agentPath = config('services.agent.path');
        $this->model = config('services.agent.model');
    }

    public function start(string $searchId, string $query): void
    {
        $metaPath = $this->metaPath($searchId);

        Storage::disk('local')->makeDirectory('searches');

        $escapedQuery = escapeshellarg($query);
        $resultAbsPath = storage_path("app/searches/{$searchId}.result.json");

        $command = sprintf(
            '%s --agent %s -p %s --output-format json --model %s --dangerously-skip-permissions --no-session-persistence > %s 2>/dev/null &',
            escapeshellarg($this->claudeBin),
            escapeshellarg($this->agentPath),
            $escapedQuery,
            escapeshellarg($this->model),
            escapeshellarg($resultAbsPath)
        );

        $shellResult = Process::run("bash -c '{$command} echo \$!'");
        $pid = trim($shellResult->output());

        Storage::disk('local')->put($metaPath, json_encode([
            'pid' => $pid,
            'query' => $query,
            'started_at' => time(),
        ], JSON_THROW_ON_ERROR));
    }

    public function isComplete(string $searchId): bool
    {
        $resultPath = $this->resultPath($searchId);

        if (! Storage::disk('local')->exists($resultPath)) {
            return false;
        }

        $content = Storage::disk('local')->get($resultPath);

        return strlen($content) > 10;
    }

    /**
     * @return array<string, mixed>|null
     */
    public function getResult(string $searchId): ?array
    {
        if (! $this->isComplete($searchId)) {
            return null;
        }

        $content = Storage::disk('local')->get($this->resultPath($searchId));

        $decoded = json_decode($content, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return null;
        }

        return $decoded;
    }

    public function cancel(string $searchId): void
    {
        $metaPath = $this->metaPath($searchId);

        if (Storage::disk('local')->exists($metaPath)) {
            $meta = json_decode(Storage::disk('local')->get($metaPath), true);
            if (! empty($meta['pid'])) {
                Process::run("kill {$meta['pid']} 2>/dev/null");
            }
        }

        Storage::disk('local')->delete([$this->metaPath($searchId), $this->resultPath($searchId)]);
    }

    public function cleanup(int $maxAgeHours = 24): int
    {
        $disk = Storage::disk('local');
        $files = $disk->files('searches');
        $threshold = time() - ($maxAgeHours * 3600);
        $removed = 0;

        foreach ($files as $file) {
            if ($disk->lastModified($file) < $threshold) {
                $disk->delete($file);
                $removed++;
            }
        }

        return $removed;
    }

    private function metaPath(string $searchId): string
    {
        return "searches/{$searchId}.meta.json";
    }

    private function resultPath(string $searchId): string
    {
        return "searches/{$searchId}.result.json";
    }
}

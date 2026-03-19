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

        $resultAbsPath = Storage::disk('local')->path("searches/{$searchId}.result.json");
        $stderrPath = Storage::disk('local')->path("searches/{$searchId}.stderr.log");
        $pidFile = Storage::disk('local')->path("searches/{$searchId}.pid");

        $mcpTools = implode(',', [
            'mcp__plugin_stj-vec-tools_stj-vec-tools__search',
            'mcp__plugin_stj-vec-tools_stj-vec-tools__document',
            'mcp__plugin_stj-vec-tools_stj-vec-tools__filters',
        ]);

        $command = implode(' ', [
            escapeshellarg($this->claudeBin),
            '--agent', escapeshellarg($this->agentPath),
            '-p', escapeshellarg($query),
            '--output-format', 'json',
            '--model', escapeshellarg($this->model),
            '--tools', escapeshellarg($mcpTools),
            '--dangerously-skip-permissions',
        ]);

        $wrapper = sprintf(
            '(%s > %s 2> %s) & echo $! > %s',
            $command,
            escapeshellarg($resultAbsPath),
            escapeshellarg($stderrPath),
            escapeshellarg($pidFile)
        );

        Process::run(['bash', '-c', $wrapper]);

        $pid = file_exists($pidFile) ? trim(file_get_contents($pidFile)) : '';
        @unlink($pidFile);

        Storage::disk('local')->put($metaPath, json_encode([
            'pid' => $pid,
            'query' => $query,
            'started_at' => time(),
        ], JSON_THROW_ON_ERROR));
    }

    public function isComplete(string $searchId): bool
    {
        return $this->getResult($searchId) !== null;
    }

    /**
     * Parse result file. The CLI --output-format json outputs a single JSON
     * object with type="result" and the agent's text in the `result` field.
     * The agent is expected to produce a JSON string with {results: [...]}.
     *
     * @return array<string, mixed>|null
     */
    public function getResult(string $searchId): ?array
    {
        $resultPath = $this->resultPath($searchId);

        if (! Storage::disk('local')->exists($resultPath)) {
            return null;
        }

        $content = Storage::disk('local')->get($resultPath);

        if (empty(trim($content))) {
            return null;
        }

        $outer = json_decode($content, true);

        if (json_last_error() !== JSON_ERROR_NONE || ! is_array($outer)) {
            return null;
        }

        // CLI outputs a single object with type="result"
        $resultText = null;
        if (isset($outer['type']) && $outer['type'] === 'result' && isset($outer['result'])) {
            $resultText = $outer['result'];
        }

        if ($resultText === null || ! is_string($resultText)) {
            return null;
        }

        // Strip code fences (```json ... ```) if present
        $resultText = trim($resultText);
        if (str_starts_with($resultText, '```')) {
            $resultText = substr($resultText, strpos($resultText, "\n") + 1);
        }
        if (str_ends_with($resultText, '```')) {
            $resultText = substr($resultText, 0, strrpos($resultText, '```'));
        }
        $resultText = trim($resultText);

        $inner = json_decode($resultText, true);

        if (json_last_error() !== JSON_ERROR_NONE || ! isset($inner['results'])) {
            return null;
        }

        return $inner;
    }

    public function isProcessDead(string $searchId): bool
    {
        $metaPath = $this->metaPath($searchId);

        if (! Storage::disk('local')->exists($metaPath)) {
            return true;
        }

        $meta = json_decode(Storage::disk('local')->get($metaPath), true);
        $pid = (int) ($meta['pid'] ?? 0);

        if ($pid <= 0) {
            return true;
        }

        return ! posix_kill($pid, 0);
    }

    public function cancel(string $searchId): void
    {
        $metaPath = $this->metaPath($searchId);

        if (Storage::disk('local')->exists($metaPath)) {
            $meta = json_decode(Storage::disk('local')->get($metaPath), true);
            $pid = (int) ($meta['pid'] ?? 0);
            if ($pid > 0) {
                Process::run(['kill', (string) $pid]);
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

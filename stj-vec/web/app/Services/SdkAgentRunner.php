<?php

namespace App\Services;

use Illuminate\Support\Facades\Process;
use Illuminate\Support\Facades\Storage;

class SdkAgentRunner implements AgentRunnerInterface
{
    private string $bunBin;

    private string $sdkScript;

    private string $anthropicKey;

    public function __construct()
    {
        $this->bunBin = config('services.agent.bun_bin');
        $this->sdkScript = config('services.agent.sdk_script');
        $this->anthropicKey = (string) config('services.agent.sdk_anthropic_key');
    }

    public function start(string $searchId, string $query): void
    {
        $metaPath = $this->metaPath($searchId);

        Storage::disk('local')->makeDirectory('searches');

        $resultAbsPath = Storage::disk('local')->path("searches/{$searchId}.result.json");
        $stderrPath = Storage::disk('local')->path("searches/{$searchId}.stderr.log");
        $pidFile = Storage::disk('local')->path("searches/{$searchId}.pid");

        $command = implode(' ', [
            'ANTHROPIC_API_KEY='.escapeshellarg($this->anthropicKey),
            escapeshellarg($this->bunBin),
            'run',
            escapeshellarg($this->sdkScript),
            escapeshellarg($query),
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

        $decoded = json_decode($content, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            return null;
        }

        if (! isset($decoded['results'])) {
            return null;
        }

        return $decoded;
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

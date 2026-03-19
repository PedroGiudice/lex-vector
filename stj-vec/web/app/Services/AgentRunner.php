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
            '-p', escapeshellarg($query."\n\nFORMATO OBRIGATORIO: responda EXCLUSIVAMENTE com um objeto JSON valido. Comece com { e termine com }. Sem markdown, sem texto, sem code fences. Schema: {\"original_query\": \"...\", \"decomposition\": {\"angles\": [...]}, \"results\": [...], \"total_results\": N, \"total_searches\": N}"),
            '--output-format', 'json',
            '--model', escapeshellarg($this->model),
            '--tools', escapeshellarg($mcpTools),
            '--dangerously-skip-permissions',
        ]);

        $projectRoot = dirname(base_path(), 2);

        $wrapper = sprintf(
            '(cd %s && %s > %s 2> %s) & echo $! > %s',
            escapeshellarg($projectRoot),
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
     * Parse result from CLI agent session.
     *
     * Strategy: extract structured results directly from the JSONL session log
     * (tool call results), bypassing the agent's text output entirely.
     * Falls back to parsing the agent's text output if JSONL extraction fails.
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

        // Must be a CLI result envelope
        if (! isset($outer['type']) || $outer['type'] !== 'result') {
            return null;
        }

        // Strategy 1: extract from JSONL session log (imposed structure)
        $sessionId = $outer['session_id'] ?? null;
        if ($sessionId) {
            $extracted = $this->extractFromJsonl($sessionId);
            if ($extracted !== null) {
                return $extracted;
            }
        }

        // Strategy 2: try parsing agent's text as JSON
        $resultText = $outer['result'] ?? null;
        if (is_string($resultText)) {
            $resultText = trim($resultText);

            // Strip code fences
            if (str_starts_with($resultText, '```')) {
                $resultText = substr($resultText, strpos($resultText, "\n") + 1);
            }
            if (str_ends_with($resultText, '```')) {
                $resultText = substr($resultText, 0, strrpos($resultText, '```'));
            }
            $resultText = trim($resultText);

            $inner = json_decode($resultText, true);
            if (json_last_error() === JSON_ERROR_NONE && isset($inner['results'])) {
                return $inner;
            }

            // Strategy 3: narrative fallback
            return ['narrative' => $resultText];
        }

        return null;
    }

    /**
     * Extract structured search results from the CLI session JSONL log.
     *
     * Reads tool_use (search queries) and tool_result (search responses)
     * from the session log, bypassing the agent's text output entirely.
     *
     * @return array<string, mixed>|null
     */
    private function extractFromJsonl(string $sessionId): ?array
    {
        $home = getenv('HOME') ?: '/home/opc';
        $jsonlPath = $home.'/.claude/projects/-home-opc-lex-vector/'.$sessionId.'.jsonl';

        if (! file_exists($jsonlPath)) {
            return null;
        }

        $searchQueries = [];
        $allResults = [];

        $handle = fopen($jsonlPath, 'r');
        if (! $handle) {
            return null;
        }

        while (($line = fgets($handle)) !== false) {
            $entry = json_decode(trim($line), true);
            if (! is_array($entry)) {
                continue;
            }

            // Track search queries from tool_use
            if (($entry['type'] ?? '') === 'assistant') {
                foreach ($entry['message']['content'] ?? [] as $block) {
                    if (($block['type'] ?? '') === 'tool_use'
                        && str_contains($block['name'] ?? '', 'search')) {
                        $searchQueries[] = $block['input']['query'] ?? '';
                    }
                }
            }

            // Extract results from tool_result
            if (($entry['type'] ?? '') === 'user') {
                $userContent = $entry['message']['content'] ?? [];
                if (! is_array($userContent)) {
                    continue;
                }
                foreach ($userContent as $block) {
                    if (($block['type'] ?? '') !== 'tool_result') {
                        continue;
                    }

                    $resultContent = $block['content'] ?? '';

                    // content can be string or array of {type: "text", text: "..."}
                    $texts = [];
                    if (is_string($resultContent)) {
                        $texts[] = $resultContent;
                    } elseif (is_array($resultContent)) {
                        foreach ($resultContent as $item) {
                            if (is_array($item) && ($item['type'] ?? '') === 'text') {
                                $texts[] = $item['text'];
                            }
                        }
                    }

                    foreach ($texts as $text) {
                        $data = json_decode($text, true);
                        if (is_array($data) && isset($data['results']) && is_array($data['results'])) {
                            $allResults = array_merge($allResults, $data['results']);
                        }
                    }
                }
            }
        }

        fclose($handle);

        if (empty($allResults)) {
            return null;
        }

        // Deduplicate by doc_id
        $seen = [];
        $unique = [];
        foreach ($allResults as $result) {
            $docId = $result['doc_id'] ?? '';
            if ($docId && ! isset($seen[$docId])) {
                $seen[$docId] = true;
                $unique[] = $result;
            }
        }

        // Build angles from search queries
        $angles = array_map(fn (string $query) => [
            'query' => $query,
            'angle' => $query,
            'results_count' => 0,
        ], $searchQueries);

        return [
            'decomposition' => [
                'intent' => 'exploratoria',
                'angles' => $angles,
                'rounds' => 1,
            ],
            'results' => array_map(function ($r) {
                return [
                    'doc_id' => $r['doc_id'] ?? '',
                    'processo' => $r['processo'] ?? '',
                    'classe' => $r['classe'] ?? '',
                    'ministro' => $r['ministro'] ?? '',
                    'data_publicacao' => $r['data_publicacao'] ?? '',
                    'tipo' => $r['tipo'] ?? '',
                    'orgao_julgador' => $r['orgao_julgador'] ?? '',
                    'content_preview' => mb_substr($r['content'] ?? '', 0, 300),
                    'scores' => $r['scores'] ?? [],
                    'found_via' => '',
                ];
            }, $unique),
            'total_results' => count($unique),
            'total_searches' => count($searchQueries),
        ];
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

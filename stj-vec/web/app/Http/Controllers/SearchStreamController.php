<?php

namespace App\Http\Controllers;

use Illuminate\Support\Facades\Storage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class SearchStreamController extends Controller
{
    private const TIMEOUT_SECONDS = 600;

    private const HEARTBEAT_INTERVAL_US = 500_000;

    public function stream(string $searchId): StreamedResponse
    {
        $metaPath = "searches/{$searchId}.meta.json";

        if (! Storage::disk('local')->exists($metaPath)) {
            abort(404);
        }

        $stderrPath = Storage::disk('local')->path("searches/{$searchId}.stderr.log");
        $resultPath = "searches/{$searchId}.result.json";

        return new StreamedResponse(function () use ($searchId, $stderrPath, $resultPath) {
            // Ensure output is flushed immediately to the client (SSE requirement)
            ob_implicit_flush(true);

            $stderrPos = 0;
            $startTime = time();

            while (true) {
                if (connection_aborted()) {
                    break;
                }

                // Read new stderr lines (NDJSON events from agent)
                if (file_exists($stderrPath)) {
                    $fh = fopen($stderrPath, 'r');
                    if ($fh) {
                        fseek($fh, $stderrPos);
                        while (($line = fgets($fh)) !== false) {
                            $line = trim($line);
                            if ($line === '') {
                                continue;
                            }
                            $decoded = json_decode($line, true);
                            if (json_last_error() === JSON_ERROR_NONE && isset($decoded['event'])) {
                                $eventName = $decoded['event'];
                                echo "event: {$eventName}\ndata: {$line}\n\n";
                                flush();

                                if ($eventName === 'error') {
                                    return;
                                }

                                // On 'completed' from agent, wait for result.json to be non-empty
                                // (Bun may flush stdout slightly after stderr)
                                if ($eventName === 'completed') {
                                    for ($wait = 0; $wait < 10; $wait++) {
                                        if (Storage::disk('local')->exists($resultPath)) {
                                            $resultContent = Storage::disk('local')->get($resultPath);
                                            if (! empty(trim($resultContent))) {
                                                return;
                                            }
                                        }
                                        usleep(200_000);
                                    }

                                    return;
                                }
                            }
                        }
                        $stderrPos = ftell($fh);
                        fclose($fh);
                    }
                }

                // Check if result file appeared (covers CLI driver with no NDJSON events)
                if (Storage::disk('local')->exists($resultPath)) {
                    $content = Storage::disk('local')->get($resultPath);
                    $parsed = $this->parseResultContent($content);
                    if ($parsed !== null) {
                        $syntheticEvent = json_encode([
                            'event' => 'completed',
                            'total_results' => count($parsed['results']),
                            'synthetic' => true,
                            'timestamp' => time() * 1000,
                        ]);
                        echo "event: completed\ndata: {$syntheticEvent}\n\n";
                        flush();

                        return;
                    }
                }

                // Check process dead (no result + process gone = error)
                if ($this->isProcessDead($searchId) && ! Storage::disk('local')->exists($resultPath)) {
                    $errorEvent = json_encode([
                        'event' => 'error',
                        'message' => 'Process died without producing results',
                        'timestamp' => time() * 1000,
                    ]);
                    echo "event: error\ndata: {$errorEvent}\n\n";
                    ob_flush();
                    flush();

                    return;
                }

                // Server-side timeout
                if ((time() - $startTime) > self::TIMEOUT_SECONDS) {
                    $timeoutEvent = json_encode([
                        'event' => 'timeout',
                        'message' => 'Server-side timeout exceeded',
                        'timestamp' => time() * 1000,
                    ]);
                    echo "event: timeout\ndata: {$timeoutEvent}\n\n";
                    ob_flush();
                    flush();

                    return;
                }

                // Heartbeat
                echo ": heartbeat\n\n";
                flush();

                usleep(self::HEARTBEAT_INTERVAL_US);
            }
        }, 200, [
            'Content-Type' => 'text/event-stream',
            'Cache-Control' => 'no-cache',
            'X-Accel-Buffering' => 'no',
            'Connection' => 'keep-alive',
        ]);
    }

    /**
     * Parse result file content supporting both formats:
     * - SDK format: JSON object with top-level "results" key
     * - CLI format: JSON array from --output-format json; last element with type="result"
     *   contains the agent output as a JSON string in the "result" field
     *
     * @return array<string, mixed>|null
     */
    private function parseResultContent(string $content): ?array
    {
        if (empty(trim($content))) {
            return null;
        }

        $decoded = json_decode($content, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            return null;
        }

        // SDK format: direct JSON object with "results"
        if (is_array($decoded) && isset($decoded['results'])) {
            return $decoded;
        }

        // CLI format: JSON array of message objects
        if (is_array($decoded) && array_is_list($decoded)) {
            foreach (array_reverse($decoded) as $message) {
                if (isset($message['type']) && $message['type'] === 'result' && isset($message['result'])) {
                    $inner = json_decode($message['result'], true);
                    if (json_last_error() === JSON_ERROR_NONE && isset($inner['results'])) {
                        return $inner;
                    }
                }
            }
        }

        return null;
    }

    private function isProcessDead(string $searchId): bool
    {
        $metaPath = "searches/{$searchId}.meta.json";

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
}

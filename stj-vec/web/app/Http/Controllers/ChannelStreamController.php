<?php

namespace App\Http\Controllers;

use Symfony\Component\HttpFoundation\StreamedResponse;

class ChannelStreamController extends Controller
{
    private const TIMEOUT_SECONDS = 600;

    private const HEARTBEAT_INTERVAL_US = 1_000_000;

    /**
     * Proxy SSE stream from channel plugin (localhost) to browser.
     */
    public function stream(string $requestId): StreamedResponse
    {
        $channelUrl = config('services.agent.channel.url');
        $upstreamUrl = "{$channelUrl}/stream/{$requestId}";

        return new StreamedResponse(function () use ($upstreamUrl, $requestId) {
            ob_implicit_flush(true);

            $ctx = stream_context_create([
                'http' => [
                    'timeout' => self::TIMEOUT_SECONDS,
                    'header' => "Accept: text/event-stream\r\n",
                ],
            ]);

            $upstream = @fopen($upstreamUrl, 'r', false, $ctx);

            if (! $upstream) {
                echo 'data: '.json_encode(['type' => 'error', 'request_id' => $requestId, 'message' => 'Failed to connect to channel'])."\n\n";
                flush();

                return;
            }

            stream_set_blocking($upstream, false);
            $startTime = time();

            while (! feof($upstream)) {
                if (connection_aborted()) {
                    break;
                }

                if ((time() - $startTime) > self::TIMEOUT_SECONDS) {
                    echo 'data: '.json_encode(['type' => 'timeout', 'request_id' => $requestId])."\n\n";
                    flush();

                    break;
                }

                $line = fgets($upstream, 8192);

                if ($line !== false && $line !== '') {
                    echo $line;
                    flush();

                    // Stop on done/timeout events
                    if (str_starts_with($line, 'data: ')) {
                        $payload = json_decode(substr($line, 6), true);
                        if (isset($payload['type']) && in_array($payload['type'], ['done', 'timeout'], true)) {
                            break;
                        }
                    }
                } else {
                    echo ": heartbeat\n\n";
                    flush();
                    usleep(self::HEARTBEAT_INTERVAL_US);
                }
            }

            @fclose($upstream);
        }, 200, [
            'Content-Type' => 'text/event-stream',
            'Cache-Control' => 'no-cache',
            'X-Accel-Buffering' => 'no',
            'Connection' => 'keep-alive',
        ]);
    }
}

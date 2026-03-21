<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Process;

class ChannelSessionManager
{
    private string $claudeBin;

    private string $channelUrl;

    private int $timeout;

    private ?int $pid = null;

    private string $pidFile;

    public function __construct()
    {
        $this->claudeBin = config('services.agent.claude_bin');
        $this->channelUrl = config('services.agent.channel.url');
        $this->timeout = config('services.agent.channel.timeout');
        $this->pidFile = storage_path('app/channel-session.pid');
    }

    public function ensureRunning(): bool
    {
        if ($this->isAlive()) {
            return true;
        }

        return $this->start();
    }

    public function isAlive(): bool
    {
        try {
            $response = Http::timeout(2)->get("{$this->channelUrl}/status");

            return $response->successful() && ($response->json('ok') === true);
        } catch (\Throwable) {
            return false;
        }
    }

    public function start(): bool
    {
        $this->stop();

        $cwd = base_path();
        $logPath = storage_path('logs/channel-session.log');

        $command = sprintf(
            'cd %s && nohup %s --dangerously-load-development-channels server:stj-channel --dangerously-skip-permissions > %s 2>&1 & echo $!',
            escapeshellarg($cwd),
            escapeshellarg($this->claudeBin),
            escapeshellarg($logPath),
        );

        $result = Process::run(['bash', '-c', $command]);
        $pid = (int) trim($result->output());

        if ($pid <= 0) {
            Log::error('ChannelSessionManager: failed to start claude', ['output' => $result->output()]);

            return false;
        }

        file_put_contents($this->pidFile, (string) $pid);
        $this->pid = $pid;

        for ($i = 0; $i < 60; $i++) {
            if ($this->isAlive()) {
                Log::info('ChannelSessionManager: session started', ['pid' => $pid]);

                return true;
            }
            sleep(1);
        }

        Log::error('ChannelSessionManager: channel not ready after 60s');
        $this->stop();

        return false;
    }

    public function stop(): void
    {
        $pid = $this->loadPid();
        if ($pid > 0 && posix_kill($pid, 0)) {
            posix_kill($pid, SIGTERM);
            usleep(500_000);
            if (posix_kill($pid, 0)) {
                posix_kill($pid, SIGKILL);
            }
        }

        @unlink($this->pidFile);
        $this->pid = null;
    }

    /**
     * Envia query ao channel (fire-and-forget). Retorno via SSE push.
     */
    public function sendQuery(string $query, string $requestId): string
    {
        $this->ensureRunning();

        $response = Http::timeout(10)
            ->post("{$this->channelUrl}/query", [
                'query' => $query,
                'request_id' => $requestId,
            ]);

        if (! $response->successful()) {
            throw new \RuntimeException("Channel query failed: {$response->status()}");
        }

        return $response->json('request_id');
    }

    /**
     * URL do SSE stream para um request_id.
     */
    public function streamUrl(string $requestId): string
    {
        return "{$this->channelUrl}/stream/{$requestId}";
    }

    private function loadPid(): int
    {
        if ($this->pid) {
            return $this->pid;
        }

        if (file_exists($this->pidFile)) {
            return (int) trim(file_get_contents($this->pidFile));
        }

        return 0;
    }
}

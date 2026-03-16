<?php

namespace App\Services;

interface AgentRunnerInterface
{
    /**
     * Start an agent search in the background.
     */
    public function start(string $searchId, string $query): void;

    /**
     * Check if a search has completed (result file exists).
     */
    public function isComplete(string $searchId): bool;

    /**
     * Get parsed result for a completed search.
     *
     * @return array<string, mixed>|null
     */
    public function getResult(string $searchId): ?array;

    /**
     * Check if the background process has died without producing a result.
     */
    public function isProcessDead(string $searchId): bool;

    /**
     * Cancel a running search by killing its process.
     */
    public function cancel(string $searchId): void;

    /**
     * Remove search files older than given hours.
     */
    public function cleanup(int $maxAgeHours = 24): int;
}

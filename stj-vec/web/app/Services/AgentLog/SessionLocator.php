<?php

namespace App\Services\AgentLog;

final class SessionLocator
{
    private const PROJECT_DIR = '/home/opc/.claude/projects/-home-opc-lex-vector';

    /**
     * Find JSONL file for a specific session ID.
     */
    public static function findSession(string $sessionId): ?string
    {
        $path = self::PROJECT_DIR . '/' . $sessionId . '.jsonl';

        return file_exists($path) ? $path : null;
    }

    /**
     * List recent JSONL session files, sorted by modification time (newest first).
     *
     * @return array<int, array{path: string, session_id: string, modified_at: int, size: int}>
     */
    public static function listRecent(int $limit = 10): array
    {
        $dir = self::PROJECT_DIR;
        if (! is_dir($dir)) {
            return [];
        }

        $files = glob($dir . '/*.jsonl');
        if ($files === false) {
            return [];
        }

        // Filter out non-session files (skill-injections, etc.)
        $sessions = [];
        foreach ($files as $file) {
            $basename = basename($file, '.jsonl');
            // Session IDs are UUIDs
            if (! preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/', $basename)) {
                continue;
            }
            $sessions[] = [
                'path' => $file,
                'session_id' => $basename,
                'modified_at' => filemtime($file),
                'size' => filesize($file),
            ];
        }

        // Sort by modification time descending
        usort($sessions, fn ($a, $b) => $b['modified_at'] <=> $a['modified_at']);

        return array_slice($sessions, 0, $limit);
    }
}

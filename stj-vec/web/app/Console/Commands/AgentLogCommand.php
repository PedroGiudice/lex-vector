<?php

namespace App\Console\Commands;

use App\DTOs\AgentLogEntry;
use App\DTOs\ContentBlock;
use App\Enums\ContentType;
use App\Enums\EntryType;
use App\Services\AgentLog\JsonlParser;
use App\Services\AgentLog\SessionLocator;
use Carbon\CarbonImmutable;
use Illuminate\Console\Command;

class AgentLogCommand extends Command
{
    protected $signature = 'agent:log {session-id? : Session UUID to inspect}';

    protected $description = 'Inspect Claude CLI agent session logs';

    public function handle(): int
    {
        $sessionId = $this->argument('session-id');

        if ($sessionId === null) {
            return $this->listSessions();
        }

        return $this->showSession($sessionId);
    }

    private function listSessions(): int
    {
        $sessions = SessionLocator::listRecent(10);

        if (empty($sessions)) {
            $this->warn('Nenhuma sessao encontrada.');

            return 0;
        }

        $this->info('Sessoes recentes:');
        $this->newLine();

        foreach ($sessions as $s) {
            $date = CarbonImmutable::createFromTimestamp($s['modified_at'])->format('Y-m-d H:i:s');
            $sizeKb = round($s['size'] / 1024);

            // Quick peek at first user message
            $preview = $this->peekFirstUserMessage($s['path']);

            $this->line(sprintf(
                '  <fg=cyan>%s</>  %s  %sKB  %s',
                $s['session_id'],
                $date,
                $sizeKb,
                $preview ? '<fg=gray>' . mb_substr($preview, 0, 60) . '</>' : '',
            ));
        }

        $this->newLine();
        $this->line('Uso: <fg=yellow>php artisan agent:log <session-id></>');

        return 0;
    }

    private function showSession(string $sessionId): int
    {
        $path = SessionLocator::findSession($sessionId);

        if ($path === null) {
            $this->error("Sessao nao encontrada: {$sessionId}");

            return 1;
        }

        $entries = JsonlParser::parseFile($path);

        if (empty($entries)) {
            $this->warn('Sessao vazia.');

            return 0;
        }

        $this->info(sprintf('Sessao: %s (%d entradas)', $sessionId, count($entries)));
        $this->newLine();

        $toolCallCount = 0;
        $firstTimestamp = $entries[0]->timestamp;

        foreach ($entries as $entry) {
            $elapsed = $entry->timestamp->diffInSeconds($firstTimestamp);
            $timeLabel = sprintf('+%ds', $elapsed);

            match ($entry->type) {
                EntryType::User => $this->renderUserEntry($entry, $timeLabel),
                EntryType::Assistant => $this->renderAssistantEntry($entry, $timeLabel, $toolCallCount),
                EntryType::System => null, // skip system entries
                default => null,
            };

            $toolCallCount += count($entry->toolCalls);
        }

        $this->newLine();
        $this->renderSummary($entries);

        return 0;
    }

    private function renderUserEntry(AgentLogEntry $entry, string $timeLabel): void
    {
        $text = is_string($entry->content)
            ? mb_substr(trim($entry->content), 0, 200)
            : '[content blocks]';

        // Skip tool results (they come as user entries)
        if (is_array($entry->content)) {
            $hasToolResult = false;
            foreach ($entry->content as $block) {
                if ($block->type === ContentType::ToolResult) {
                    $hasToolResult = true;
                    $this->renderToolResult($block, $timeLabel);
                }
            }
            if ($hasToolResult) {
                return;
            }
        }

        $this->line(sprintf('  <fg=green>%s</> <fg=white;options=bold>USER</> %s', $timeLabel, $text));
    }

    private function renderAssistantEntry(AgentLogEntry $entry, string $timeLabel, int &$toolCallCount): void
    {
        if (! is_array($entry->content)) {
            $this->line(sprintf('  <fg=green>%s</> <fg=blue;options=bold>AI</> %s', $timeLabel, mb_substr((string) $entry->content, 0, 200)));

            return;
        }

        foreach ($entry->content as $block) {
            match ($block->type) {
                ContentType::Thinking => $this->line(sprintf(
                    '  <fg=green>%s</> <fg=magenta>THINK</> %s',
                    $timeLabel,
                    mb_substr(trim($block->thinking ?? ''), 0, 120) . '...',
                )),
                ContentType::Text => $this->line(sprintf(
                    '  <fg=green>%s</> <fg=blue;options=bold>AI</> %s',
                    $timeLabel,
                    mb_substr(trim($block->text ?? ''), 0, 200),
                )),
                ContentType::ToolUse => $this->renderToolUse($block, $timeLabel),
                default => null,
            };
        }

        if ($entry->usage) {
            $input = ($entry->usage['input_tokens'] ?? 0)
                + ($entry->usage['cache_read_input_tokens'] ?? 0)
                + ($entry->usage['cache_creation_input_tokens'] ?? 0);
            $output = $entry->usage['output_tokens'] ?? 0;
            $this->line(sprintf(
                '           <fg=gray>tokens: %s in / %s out</>',
                number_format($input),
                number_format($output),
            ));
        }
    }

    private function renderToolUse(ContentBlock $block, string $timeLabel): void
    {
        $name = $block->name ?? 'unknown';
        $input = $block->input ?? [];

        // Compact display of input
        $inputSummary = match (true) {
            str_contains($name, 'search') => $input['query'] ?? json_encode($input),
            str_contains($name, 'document') => $input['doc_id'] ?? json_encode($input),
            $name === 'Read' => $input['file_path'] ?? json_encode($input),
            $name === 'Bash' => mb_substr($input['command'] ?? '', 0, 80),
            $name === 'Grep' => ($input['pattern'] ?? '') . ' ' . ($input['path'] ?? ''),
            default => mb_substr(json_encode($input, JSON_UNESCAPED_UNICODE), 0, 120),
        };

        $this->line(sprintf(
            '  <fg=green>%s</> <fg=yellow>TOOL</> <fg=white>%s</> %s',
            $timeLabel,
            $name,
            $inputSummary,
        ));
    }

    private function renderToolResult(ContentBlock $block, string $timeLabel): void
    {
        $content = $block->content;
        $preview = is_string($content)
            ? mb_substr(trim($content), 0, 150)
            : (is_array($content) ? mb_substr(json_encode($content, JSON_UNESCAPED_UNICODE), 0, 150) : '');

        $tag = ($block->isError ?? false) ? '<fg=red>ERROR</>' : '<fg=gray>RESULT</>';

        $this->line(sprintf(
            '  <fg=green>%s</> %s %s',
            $timeLabel,
            $tag,
            $preview,
        ));
    }

    private function renderSummary(array $entries): int
    {
        $toolCalls = [];
        $totalInput = 0;
        $totalOutput = 0;

        foreach ($entries as $entry) {
            foreach ($entry->toolCalls as $tc) {
                $toolCalls[$tc->name] = ($toolCalls[$tc->name] ?? 0) + 1;
            }
            if ($entry->usage) {
                $totalInput += ($entry->usage['input_tokens'] ?? 0)
                    + ($entry->usage['cache_read_input_tokens'] ?? 0)
                    + ($entry->usage['cache_creation_input_tokens'] ?? 0);
                $totalOutput += $entry->usage['output_tokens'] ?? 0;
            }
        }

        $first = $entries[0]->timestamp;
        $last = end($entries)->timestamp;
        $duration = $last->diffInSeconds($first);

        $this->info('--- Resumo ---');
        $this->line(sprintf('Duracao: %ds', $duration));
        $this->line(sprintf('Entradas: %d', count($entries)));
        $this->line(sprintf('Tokens: %s input / %s output', number_format($totalInput), number_format($totalOutput)));

        if (! empty($toolCalls)) {
            $this->line('Tool calls:');
            arsort($toolCalls);
            foreach ($toolCalls as $name => $count) {
                $this->line(sprintf('  %s: %d', $name, $count));
            }
        }

        return 0;
    }

    private function peekFirstUserMessage(string $path): ?string
    {
        $handle = fopen($path, 'r');
        if (! $handle) {
            return null;
        }

        try {
            while (($line = fgets($handle)) !== false) {
                $line = trim($line);
                if ($line === '') {
                    continue;
                }
                try {
                    $raw = json_decode($line, true, 512, JSON_THROW_ON_ERROR);
                } catch (\JsonException) {
                    continue;
                }
                if (($raw['type'] ?? '') !== 'user') {
                    continue;
                }
                $content = $raw['message']['content'] ?? '';
                if (is_string($content) && trim($content) !== '') {
                    return trim($content);
                }
            }
        } finally {
            fclose($handle);
        }

        return null;
    }
}

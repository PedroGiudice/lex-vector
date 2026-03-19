<?php

namespace App\Services\AgentLog;

use App\DTOs\AgentLogEntry;
use App\DTOs\ContentBlock;
use App\DTOs\ToolCall;
use App\Enums\ContentType;
use App\Enums\EntryType;
use Carbon\CarbonImmutable;

final class JsonlParser
{
    /**
     * @return AgentLogEntry[]
     */
    public static function parseFile(string $filePath): array
    {
        if (! file_exists($filePath)) {
            return [];
        }

        $handle = fopen($filePath, 'r');
        if (! $handle) {
            return [];
        }

        $entries = [];

        try {
            while (($line = fgets($handle)) !== false) {
                $line = trim($line);
                if ($line === '') {
                    continue;
                }

                try {
                    $raw = json_decode($line, true, 512, JSON_THROW_ON_ERROR);
                    $entry = self::parseEntry($raw);
                    if ($entry !== null) {
                        $entries[] = $entry;
                    }
                } catch (\JsonException) {
                    continue;
                }
            }
        } finally {
            fclose($handle);
        }

        return $entries;
    }

    public static function parseEntry(array $raw): ?AgentLogEntry
    {
        if (empty($raw['uuid'])) {
            return null;
        }

        $type = EntryType::tryFrom($raw['type'] ?? '');
        if ($type === null) {
            return null;
        }

        $contentBlocks = [];
        $toolCalls = [];
        $usage = null;
        $model = null;
        $stopReason = null;
        $content = '';

        if (in_array($type, [EntryType::User, EntryType::Assistant], true)) {
            $rawContent = $raw['message']['content'] ?? '';

            if (is_array($rawContent)) {
                $contentBlocks = self::parseContentBlocks($rawContent);
                $content = $contentBlocks;

                foreach ($contentBlocks as $block) {
                    if ($block->type === ContentType::ToolUse && $block->id && $block->name) {
                        $toolCalls[] = new ToolCall(
                            id: $block->id,
                            name: $block->name,
                            input: $block->input ?? [],
                        );
                    }
                }
            } else {
                $content = (string) $rawContent;
            }

            if ($type === EntryType::Assistant) {
                $usage = $raw['message']['usage'] ?? null;
                $model = $raw['message']['model'] ?? null;
                $stopReason = $raw['message']['stop_reason'] ?? null;
            }
        }

        $timestamp = ! empty($raw['timestamp'])
            ? CarbonImmutable::parse($raw['timestamp'])
            : CarbonImmutable::now();

        return new AgentLogEntry(
            uuid: $raw['uuid'],
            type: $type,
            timestamp: $timestamp,
            content: $content,
            contentBlocks: $contentBlocks,
            toolCalls: $toolCalls,
            usage: $usage,
            model: $model,
            stopReason: $stopReason,
        );
    }

    /**
     * @return ContentBlock[]
     */
    public static function parseContentBlocks(array $blocks): array
    {
        $result = [];
        foreach ($blocks as $block) {
            if (! is_array($block) || ! isset($block['type'])) {
                continue;
            }
            $ct = ContentType::tryFrom($block['type']);
            if ($ct === null) {
                continue;
            }
            $result[] = ContentBlock::fromArray($block);
        }

        return $result;
    }
}

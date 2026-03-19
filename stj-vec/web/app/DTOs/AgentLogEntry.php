<?php

namespace App\DTOs;

use App\Enums\EntryType;
use Carbon\CarbonImmutable;

final readonly class AgentLogEntry
{
    /**
     * @param  ContentBlock[]  $contentBlocks
     * @param  ToolCall[]  $toolCalls
     */
    public function __construct(
        public string $uuid,
        public EntryType $type,
        public CarbonImmutable $timestamp,
        public string|array $content,
        public array $contentBlocks,
        public array $toolCalls,
        public ?array $usage = null,
        public ?string $model = null,
        public ?string $stopReason = null,
    ) {}
}

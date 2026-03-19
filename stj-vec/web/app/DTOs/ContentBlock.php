<?php

namespace App\DTOs;

use App\Enums\ContentType;

final readonly class ContentBlock
{
    public function __construct(
        public ContentType $type,
        public ?string $text = null,
        public ?string $thinking = null,
        public ?string $id = null,
        public ?string $name = null,
        public ?array $input = null,
        public ?string $toolUseId = null,
        public string|array|null $content = null,
        public ?bool $isError = null,
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            type: ContentType::from($data['type']),
            text: $data['text'] ?? null,
            thinking: $data['thinking'] ?? null,
            id: $data['id'] ?? null,
            name: $data['name'] ?? null,
            input: $data['input'] ?? null,
            toolUseId: $data['tool_use_id'] ?? null,
            content: $data['content'] ?? null,
            isError: $data['is_error'] ?? null,
        );
    }
}

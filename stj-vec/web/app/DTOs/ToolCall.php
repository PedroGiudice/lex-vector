<?php

namespace App\DTOs;

final readonly class ToolCall
{
    public function __construct(
        public string $id,
        public string $name,
        public array $input,
    ) {}
}

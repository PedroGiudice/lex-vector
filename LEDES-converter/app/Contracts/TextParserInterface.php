<?php

namespace App\Contracts;

interface TextParserInterface
{
    /**
     * Parseia texto colado de um statement e extrai dados estruturados.
     *
     * @return array{
     *     client_name: ?string,
     *     contact_person: ?string,
     *     invoice_number: ?string,
     *     invoice_date: ?string,
     *     matter_id: ?string,
     *     matter_description: ?string,
     *     total_amount: ?float,
     *     line_items: array<int, array{description: string, amount: float}>
     * }
     */
    public function parse(string $text): array;
}

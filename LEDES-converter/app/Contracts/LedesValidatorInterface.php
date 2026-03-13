<?php

namespace App\Contracts;

use Carbon\Carbon;

interface LedesValidatorInterface
{
    /**
     * Valida dados de invoice LEDES antes da geracao.
     *
     * @param  array<string, mixed>  $data  Dados da invoice (billing_start, billing_end, line_items, afa_type, etc.)
     * @param  Carbon|null  $now  Data atual para testes (default: Carbon::today())
     * @return array{errors: array<int, string>, warnings: array<int, string>}
     */
    public function validate(array $data, ?Carbon $now = null): array;
}

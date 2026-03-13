<?php

namespace App\Services;

use App\Contracts\LedesValidatorInterface;
use Carbon\Carbon;

class LedesValidator implements LedesValidatorInterface
{
    /**
     * @param  array<string, mixed>  $data
     * @return array{errors: array<int, string>, warnings: array<int, string>}
     */
    public function validate(array $data, ?Carbon $now = null): array
    {
        $now = $now ?? Carbon::today();

        $errors = [];
        $warnings = [];

        $billingStart = Carbon::parse($data['billing_start']);
        $billingEnd = Carbon::parse($data['billing_end']);
        $afaType = $data['afa_type'] ?? 'hourly';
        $matterOpenDate = isset($data['matter_open_date']) && $data['matter_open_date'] !== null
            ? Carbon::parse($data['matter_open_date'])
            : null;

        // Regra 1: BILLING_END_DATE nao pode ser data futura
        if ($billingEnd->isAfter($now)) {
            $errors[] = "Billing End Date can't be a future date. Data informada: {$billingEnd->format('d/m/Y')}.";
        }

        // Regras por line item
        /** @var array<int, array<string, mixed>> $lineItems */
        $lineItems = $data['line_items'] ?? [];

        foreach ($lineItems as $index => $item) {
            $lineNumber = $index + 1;
            $lineItemDate = Carbon::parse($item['line_item_date']);
            $taskCode = $item['task_code'] ?? '';

            // Regra 2: LINE_ITEM_DATE >= data de abertura do matter
            if ($matterOpenDate !== null && $lineItemDate->isBefore($matterOpenDate)) {
                $errors[] = "Line item #{$lineNumber}: data ({$lineItemDate->format('d/m/Y')}) e anterior a data de abertura do matter ({$matterOpenDate->format('d/m/Y')}).";
            }

            // Regra 3: LINE_ITEM_DATE dentro do billing period
            if ($lineItemDate->isBefore($billingStart)) {
                $errors[] = "Line item #{$lineNumber}: data ({$lineItemDate->format('d/m/Y')}) e anterior ao inicio do billing period ({$billingStart->format('d/m/Y')}).";
            }

            if ($lineItemDate->isAfter($billingEnd)) {
                $errors[] = "Line item #{$lineNumber}: data ({$lineItemDate->format('d/m/Y')}) e posterior ao fim do billing period ({$billingEnd->format('d/m/Y')}).";
            }

            // Regra 4: Fixed Fee / Scheduled Fixed Fee exige task code FF01
            if (in_array($afaType, ['fixed_fee', 'scheduled_fixed_fee'], true) && $taskCode !== 'FF01') {
                $errors[] = "Line item #{$lineNumber}: Fixed Fee e Scheduled Fixed Fee AFA types devem usar Task Code FF01 (atual: {$taskCode}).";
            }
        }

        // Regra 5: Warning se > 90 dias apos billing end
        $daysSinceBillingEnd = $billingEnd->diffInDays($now, false);
        if ($daysSinceBillingEnd > 90) {
            $warnings[] = "Invoice esta sendo submetido {$daysSinceBillingEnd} dias apos o fim do billing period. Invoices submetidos apos 90 dias podem ser rejeitados.";
        }

        // Regra 6: Warning accruals ate dia 27
        if ($now->day >= 28) {
            $warnings[] = "Accrual reminder: accruals devem ser submetidos ate o dia 27 de cada mes. Hoje e dia {$now->day}.";
        }

        return [
            'errors' => $errors,
            'warnings' => $warnings,
        ];
    }
}

<?php

namespace App\Services;

use App\Contracts\LedesGeneratorInterface;

class Ledes1998BGenerator implements LedesGeneratorInterface
{
    private const HEADER = 'LEDES1998B[]';

    private const COLUMNS = 'INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|LAW_FIRM_MATTER_ID|INVOICE_TOTAL|BILLING_START_DATE|BILLING_END_DATE|INVOICE_DESCRIPTION|LINE_ITEM_NUMBER|EXP/FEE/INV_ADJ_TYPE|LINE_ITEM_NUMBER_OF_UNITS|LINE_ITEM_ADJUSTMENT_AMOUNT|LINE_ITEM_TOTAL|LINE_ITEM_DATE|LINE_ITEM_TASK_CODE|LINE_ITEM_EXPENSE_CODE|LINE_ITEM_ACTIVITY_CODE|TIMEKEEPER_ID|LINE_ITEM_DESCRIPTION|LAW_FIRM_ID|LINE_ITEM_UNIT_COST|TIMEKEEPER_NAME|TIMEKEEPER_CLASSIFICATION|CLIENT_MATTER_ID[]';

    /**
     * @param  array<string, mixed>  $data
     */
    public function generate(array $data): string
    {
        $lines = [
            self::HEADER,
            self::COLUMNS,
        ];

        $invoiceDate = $this->formatDate($data['invoice_date']);
        $billingStart = $this->formatDate($data['billing_start']);
        $billingEnd = $this->formatDate($data['billing_end']);
        $unitCost = (float) ($data['unit_cost'] ?? 0);

        /** @var array<int, array<string, mixed>> $lineItems */
        $lineItems = $data['line_items'] ?? [];

        foreach ($lineItems as $index => $item) {
            $lineItemAmount = (float) $item['amount'];
            $units = $unitCost > 0 ? $lineItemAmount / $unitCost : 0;

            $fields = [
                $invoiceDate,
                $this->sanitize((string) $data['invoice_number']),
                $this->sanitize((string) $data['client_id']),
                $this->sanitize((string) $data['law_firm_matter_id']),
                $this->formatAmount((float) $data['total']),
                $billingStart,
                $billingEnd,
                $this->sanitize((string) ($data['invoice_description'] ?? '')),
                (string) ($index + 1),
                'F',
                number_format($units, 2, '.', ''),
                '',
                $this->formatAmount($lineItemAmount),
                $invoiceDate,
                $this->sanitize((string) ($item['task_code'] ?? 'L100')),
                $this->sanitize((string) ($item['expense_code'] ?? '')),
                $this->sanitize((string) ($item['activity_code'] ?? 'A103')),
                $this->sanitize((string) $data['timekeeper_id']),
                $this->sanitize((string) $item['description']),
                $this->sanitize((string) $data['law_firm_id']),
                $this->formatAmount($unitCost),
                $this->sanitize((string) $data['timekeeper_name']),
                $this->sanitize((string) $data['timekeeper_classification']),
                $this->sanitize((string) ($data['client_matter_id'] ?? '')),
            ];

            $lines[] = implode('|', $fields).'[]';
        }

        return implode("\n", $lines)."\n";
    }

    /**
     * Formata data de Y-m-d para YYYYMMDD.
     */
    private function formatDate(string $date): string
    {
        $timestamp = strtotime($date);
        if ($timestamp === false) {
            return '';
        }

        return date('Ymd', $timestamp);
    }

    /**
     * Formata valor monetario com 2 casas decimais.
     */
    private function formatAmount(float $amount): string
    {
        return number_format($amount, 2, '.', '');
    }

    /**
     * Remove caracteres que quebram o formato LEDES (pipe, brackets).
     */
    private function sanitize(string $value): string
    {
        // Remove pipe e brackets que sao delimitadores do LEDES
        return str_replace(['|', '[', ']'], '', $value);
    }
}

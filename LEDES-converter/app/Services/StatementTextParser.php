<?php

namespace App\Services;

use App\Contracts\TextParserInterface;

class StatementTextParser implements TextParserInterface
{
    /**
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
    public function parse(string $text): array
    {
        $result = [
            'client_name' => null,
            'contact_person' => null,
            'invoice_number' => null,
            'invoice_date' => null,
            'matter_id' => null,
            'matter_description' => null,
            'total_amount' => null,
            'line_items' => [],
        ];

        if (trim($text) === '') {
            return $result;
        }

        $result['client_name'] = $this->extractClientName($text);
        $result['contact_person'] = $this->extractContactPerson($text);
        $result['invoice_number'] = $this->extractInvoiceNumber($text);
        $result['invoice_date'] = $this->extractInvoiceDate($text);
        $result['matter_id'] = $this->extractMatterId($text);
        $result['matter_description'] = $this->extractMatterDescription($text);
        $result['total_amount'] = $this->extractTotalAmount($text);
        $result['line_items'] = $this->extractLineItems($text);

        return $result;
    }

    private function extractClientName(string $text): ?string
    {
        if (preg_match('/CLIENT:\s*(.+)/i', $text, $matches)) {
            return trim($matches[1]);
        }

        return null;
    }

    private function extractContactPerson(string $text): ?string
    {
        if (preg_match('/Contact\s+Person:\s*(.+)/i', $text, $matches)) {
            return trim($matches[1]);
        }

        return null;
    }

    private function extractInvoiceNumber(string $text): ?string
    {
        if (preg_match('/Invoice:\s*#?(\d+)/i', $text, $matches)) {
            return $matches[1];
        }

        return null;
    }

    private function extractInvoiceDate(string $text): ?string
    {
        if (preg_match('/Date\s+of\s+Issuance:\s*(.+)/i', $text, $matches)) {
            $dateStr = trim($matches[1]);

            $timestamp = strtotime($dateStr);
            if ($timestamp !== false) {
                return date('Y-m-d', $timestamp);
            }
        }

        return null;
    }

    private function extractMatterId(string $text): ?string
    {
        // Match "Matter ID: LS-2026-24561" or similar patterns
        if (preg_match('/Matter\s+ID:\s*(LS-\d{4}-\d+)/i', $text, $matches)) {
            return trim($matches[1]);
        }

        // Also try to find matter_id pattern anywhere in text (e.g. inline references)
        if (preg_match('/\b(LS-\d{4}-\d{4,})\b/', $text, $matches)) {
            return trim($matches[1]);
        }

        return null;
    }

    private function extractMatterDescription(string $text): ?string
    {
        if (preg_match('/Matter:\s*(.+)/i', $text, $matches)) {
            return trim($matches[1]);
        }

        return null;
    }

    private function extractTotalAmount(string $text): ?float
    {
        // Match "Total Gross Amount: US $2,400" or "US $2,400.00"
        if (preg_match('/Total\s+Gross\s+Amount:\s*US\s*\$\s*([\d,]+(?:\.\d{2})?)/i', $text, $matches)) {
            return (float) str_replace(',', '', $matches[1]);
        }

        return null;
    }

    /**
     * @return array<int, array{description: string, amount: float}>
     */
    private function extractLineItems(string $text): array
    {
        $items = [];

        // Match lines with descriptions followed by US $amount
        // Pattern: text that ends with US $X,XXX.XX
        if (preg_match_all('/^(.+?)\s+US\s*\$\s*([\d,]+(?:\.\d{2})?)\s*$/mi', $text, $matches, PREG_SET_ORDER)) {
            foreach ($matches as $match) {
                $description = trim($match[1]);
                $amount = (float) str_replace(',', '', $match[2]);

                // Skip the "Total Gross Amount" line
                if (stripos($description, 'Total Gross Amount') !== false) {
                    continue;
                }

                $items[] = [
                    'description' => $description,
                    'amount' => $amount,
                ];
            }
        }

        return $items;
    }
}

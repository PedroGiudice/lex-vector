<?php

namespace Tests\Unit;

use App\Contracts\LedesGeneratorInterface;
use App\Services\Ledes1998BGenerator;
use PHPUnit\Framework\TestCase;

class Ledes1998BGeneratorTest extends TestCase
{
    private LedesGeneratorInterface $generator;

    protected function setUp(): void
    {
        parent::setUp();
        $this->generator = new Ledes1998BGenerator;
    }

    public function test_generates_valid_ledes_header(): void
    {
        $output = $this->generator->generate($this->getSampleData());

        $lines = explode("\n", $output);
        $this->assertSame('LEDES1998B[]', $lines[0]);
    }

    public function test_generates_correct_column_headers(): void
    {
        $output = $this->generator->generate($this->getSampleData());

        $lines = explode("\n", $output);
        $this->assertStringStartsWith('INVOICE_DATE|', $lines[1]);
        $this->assertStringEndsWith('CLIENT_MATTER_ID[]', $lines[1]);
    }

    public function test_generates_pipe_delimited_data(): void
    {
        $output = $this->generator->generate($this->getSampleData());

        $lines = explode("\n", $output);
        $dataLine = $lines[2];

        // 24 campos = 23 pipes
        $this->assertSame(23, substr_count($dataLine, '|'));
    }

    public function test_formats_dates_as_yyyymmdd(): void
    {
        $output = $this->generator->generate($this->getSampleData());

        $lines = explode("\n", $output);
        $fields = explode('|', str_replace('[]', '', $lines[2]));

        // INVOICE_DATE deve ser YYYYMMDD
        $this->assertMatchesRegularExpression('/^\d{8}$/', $fields[0]);
        $this->assertSame('20260311', $fields[0]);
    }

    public function test_formats_amounts_with_two_decimals(): void
    {
        $output = $this->generator->generate($this->getSampleData());

        $lines = explode("\n", $output);
        $fields = explode('|', str_replace('[]', '', $lines[2]));

        // INVOICE_TOTAL (indice 4)
        $this->assertSame('2400.00', $fields[4]);
        // LINE_ITEM_TOTAL (indice 12)
        $this->assertSame('2400.00', $fields[12]);
    }

    public function test_calculates_units_from_total_and_rate(): void
    {
        $output = $this->generator->generate($this->getSampleData());

        $lines = explode("\n", $output);
        $fields = explode('|', str_replace('[]', '', $lines[2]));

        // LINE_ITEM_NUMBER_OF_UNITS (indice 10): 2400 / 300 = 8.00
        $this->assertSame('8.00', $fields[10]);
    }

    public function test_each_line_ends_with_brackets(): void
    {
        $output = $this->generator->generate($this->getSampleData());

        $lines = array_filter(explode("\n", $output), fn (string $line): bool => $line !== '');
        foreach ($lines as $line) {
            $this->assertStringEndsWith('[]', $line);
        }
    }

    public function test_sanitizes_non_ascii_characters(): void
    {
        $data = $this->getSampleData();
        $data['line_items'][0]['description'] = 'Defesa com caracter especial: |[]';

        $output = $this->generator->generate($data);

        // Pipes e brackets dentro de descricoes devem ser removidos
        $lines = explode("\n", $output);
        $dataLine = $lines[2];

        // O conteudo da descricao nao deve ter pipe ou [] extras
        // A linha deve ter exatamente 23 pipes (24 campos)
        $this->assertSame(23, substr_count($dataLine, '|'));
    }

    public function test_generates_multiple_line_items(): void
    {
        $data = $this->getSampleData();
        $data['line_items'][] = [
            'description' => 'Research case law',
            'amount' => 600.00,
            'task_code' => 'L110',
            'activity_code' => 'A102',
        ];
        $data['total'] = 3000.00;

        $output = $this->generator->generate($data);

        $lines = array_filter(explode("\n", $output), fn (string $line): bool => $line !== '');
        // header + column header + 2 data lines = 4
        $this->assertCount(4, $lines);
    }

    /**
     * @return array<string, mixed>
     */
    private function getSampleData(): array
    {
        return [
            'invoice_date' => '2026-03-11',
            'invoice_number' => '4212',
            'client_id' => 'Salesforce, Inc.',
            'law_firm_matter_id' => 'LS-2026-24561',
            'client_matter_id' => 'LS-2026-24561',
            'total' => 2400.00,
            'billing_start' => '2026-03-01',
            'billing_end' => '2026-03-31',
            'invoice_description' => 'Guilherme dos Santos Lima v. Salesforce - March 2026',
            'timekeeper_id' => 'CMR',
            'timekeeper_name' => 'RODRIGUES, CARLOS MAGNO',
            'timekeeper_classification' => 'PARTNR',
            'law_firm_id' => 'SF004554',
            'unit_cost' => 300.00,
            'line_items' => [
                [
                    'description' => 'Draft and file a defense and appear in court for the hearing in which we reached a settlement',
                    'amount' => 2400.00,
                    'task_code' => 'L120',
                    'activity_code' => 'A106',
                ],
            ],
        ];
    }
}

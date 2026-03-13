<?php

namespace Tests\Unit;

use App\Contracts\TextParserInterface;
use App\Services\StatementTextParser;
use PHPUnit\Framework\TestCase;

class StatementTextParserTest extends TestCase
{
    private TextParserInterface $parser;

    protected function setUp(): void
    {
        parent::setUp();
        $this->parser = new StatementTextParser;
    }

    public function test_parses_client_name(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertSame('SALESFORCE.COM, INC.', $result['client_name']);
    }

    public function test_parses_invoice_number(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertSame('4212', $result['invoice_number']);
    }

    public function test_parses_invoice_date(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertSame('2026-03-11', $result['invoice_date']);
    }

    public function test_parses_matter_description(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertSame('Guilherme dos Santos Lima v. Salesforce', $result['matter_description']);
    }

    public function test_parses_total_amount(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertSame(2400.00, $result['total_amount']);
    }

    public function test_parses_service_description(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertNotEmpty($result['line_items']);
        $this->assertStringContainsString('Draft and file a defense', $result['line_items'][0]['description']);
    }

    public function test_parses_line_item_amount(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertSame(2400.00, $result['line_items'][0]['amount']);
    }

    public function test_returns_empty_structure_for_empty_text(): void
    {
        $result = $this->parser->parse('');

        $this->assertNull($result['client_name']);
        $this->assertNull($result['invoice_number']);
        $this->assertEmpty($result['line_items']);
    }

    public function test_parses_contact_person(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertSame('Caitlin May', $result['contact_person']);
    }

    public function test_extracts_matter_id_from_text(): void
    {
        $text = $this->getSampleTextWithMatterId();
        $result = $this->parser->parse($text);

        $this->assertSame('LS-2026-24561', $result['matter_id']);
    }

    public function test_returns_null_matter_id_when_not_present(): void
    {
        $text = $this->getSampleText();
        $result = $this->parser->parse($text);

        $this->assertNull($result['matter_id']);
    }

    public function test_extracts_matter_id_with_different_formats(): void
    {
        $text = "Matter ID: LS-2025-22672\nMatter: General Employment Advice";
        $result = $this->parser->parse($text);

        $this->assertSame('LS-2025-22672', $result['matter_id']);
    }

    private function getSampleText(): string
    {
        return <<<'TEXT'
CLIENT: SALESFORCE.COM, INC.
50 Freemont St. Suite 300
San Francisco CA USA 94105 2231
Date of Issuance: March 11, 2026
Contact Person: Caitlin May
Invoice: #4212
Matter: Guilherme dos Santos Lima v. Salesforce
Description of Services Rendered to Salesforce Tecnologia Ltda. – General Employment Advice
Draft and file a defense and appear in court for the hearing in which we reached a settlement US $2,400.00
Total Gross Amount: US $2,400 (two thousand four hundred US dollars)
TEXT;
    }

    private function getSampleTextWithMatterId(): string
    {
        return <<<'TEXT'
CLIENT: SALESFORCE.COM, INC.
50 Freemont St. Suite 300
San Francisco CA USA 94105 2231
Date of Issuance: March 11, 2026
Contact Person: Caitlin May
Invoice: #4212
Matter ID: LS-2026-24561
Matter: Guilherme dos Santos Lima v. Salesforce
Description of Services Rendered to Salesforce Tecnologia Ltda. – General Employment Advice
Draft and file a defense and appear in court for the hearing in which we reached a settlement US $2,400.00
Total Gross Amount: US $2,400 (two thousand four hundred US dollars)
TEXT;
    }
}

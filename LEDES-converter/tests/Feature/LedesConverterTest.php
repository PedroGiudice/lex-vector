<?php

namespace Tests\Feature;

use App\Livewire\LedesConverter;
use App\Models\Matter;
use App\Models\Timekeeper;
use Database\Seeders\UtbmsSeeder;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Livewire\Livewire;
use Tests\TestCase;

class LedesConverterTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        $this->withoutVite();
        $this->seed(UtbmsSeeder::class);
    }

    public function test_home_page_loads(): void
    {
        $response = $this->get('/');

        $response->assertStatus(200);
        $response->assertSee('LEDES Converter');
    }

    public function test_livewire_component_renders(): void
    {
        Livewire::test(LedesConverter::class)
            ->assertSee('Colar Texto do Statement');
    }

    public function test_parse_text_extracts_data(): void
    {
        Timekeeper::factory()->create([
            'timekeeper_id_code' => 'CMR',
            'name' => 'RODRIGUES, CARLOS MAGNO',
            'classification' => 'PARTNR',
            'hourly_rate' => 300.00,
            'law_firm_id' => 'SF004554',
        ]);

        Livewire::test(LedesConverter::class)
            ->set('rawText', $this->getSampleText())
            ->call('parseText')
            ->assertSet('step', 'preview')
            ->assertSet('clientName', 'SALESFORCE.COM, INC.')
            ->assertSet('invoiceNumber', '4212')
            ->assertSet('totalAmount', 2400.00);
    }

    public function test_parse_text_requires_minimum_length(): void
    {
        Livewire::test(LedesConverter::class)
            ->set('rawText', 'short')
            ->call('parseText')
            ->assertHasErrors(['rawText']);
    }

    public function test_generate_ledes_creates_output(): void
    {
        $timekeeper = Timekeeper::factory()->create([
            'timekeeper_id_code' => 'CMR',
            'name' => 'RODRIGUES, CARLOS MAGNO',
            'classification' => 'PARTNR',
            'hourly_rate' => 300.00,
            'law_firm_id' => 'SF004554',
        ]);

        Livewire::test(LedesConverter::class)
            ->set('rawText', $this->getSampleText())
            ->call('parseText')
            ->set('lawFirmMatterId', 'LS-2026-24561')
            ->set('clientMatterId', 'LS-2026-24561')
            // Ajustar para datas consistentes: invoice date dentro do billing period
            ->set('billingStart', '2026-02-01')
            ->set('billingEnd', '2026-02-28')
            ->set('invoiceDate', '2026-02-15')
            ->set('lineItems', [
                ['description' => 'Legal services', 'amount' => 2400.00],
            ])
            ->call('generateLedes')
            ->assertSet('step', 'generate')
            ->assertSee('LEDES1998B[]');
    }

    public function test_generate_ledes_persists_invoice(): void
    {
        $timekeeper = Timekeeper::factory()->create([
            'timekeeper_id_code' => 'CMR',
            'name' => 'RODRIGUES, CARLOS MAGNO',
            'classification' => 'PARTNR',
            'hourly_rate' => 300.00,
            'law_firm_id' => 'SF004554',
        ]);

        Livewire::test(LedesConverter::class)
            ->set('rawText', $this->getSampleText())
            ->call('parseText')
            ->set('lawFirmMatterId', 'LS-2026-24561')
            // Ajustar para datas consistentes
            ->set('billingStart', '2026-02-01')
            ->set('billingEnd', '2026-02-28')
            ->set('invoiceDate', '2026-02-15')
            ->set('lineItems', [
                ['description' => 'Legal services', 'amount' => 2400.00],
            ])
            ->call('generateLedes');

        $this->assertDatabaseHas('invoices', [
            'invoice_number' => '4212',
        ]);

        $this->assertDatabaseHas('invoice_line_items', [
            'line_number' => 1,
        ]);
    }

    public function test_generate_requires_timekeeper(): void
    {
        Livewire::test(LedesConverter::class)
            ->set('step', 'preview')
            ->set('invoiceNumber', '4212')
            ->set('invoiceDate', '2026-03-11')
            ->set('totalAmount', 2400.00)
            ->set('billingStart', '2026-03-01')
            ->set('billingEnd', '2026-03-31')
            ->set('lawFirmMatterId', 'LS-2026')
            ->set('timekeeperId', null)
            ->call('generateLedes')
            ->assertHasErrors(['timekeeperId']);
    }

    // -------------------------------------------------------
    // Testes de integracao da validacao LEDES
    // -------------------------------------------------------

    public function test_blocks_generation_with_future_billing_end(): void
    {
        $timekeeper = Timekeeper::factory()->create([
            'timekeeper_id_code' => 'CMR',
            'name' => 'RODRIGUES, CARLOS MAGNO',
            'classification' => 'PARTNR',
            'hourly_rate' => 300.00,
            'law_firm_id' => 'SF004554',
        ]);

        Livewire::test(LedesConverter::class)
            ->set('step', 'preview')
            ->set('invoiceNumber', '4212')
            ->set('invoiceDate', '2026-03-11')
            ->set('totalAmount', 2400.00)
            ->set('billingStart', '2026-03-01')
            ->set('billingEnd', '2026-12-31') // Data futura
            ->set('lawFirmMatterId', 'LS-2026')
            ->set('timekeeperId', $timekeeper->id)
            ->set('lineItems', [
                ['description' => 'Legal services', 'amount' => 2400.00],
            ])
            ->set('taskCodes', ['L120'])
            ->set('activityCodes', ['A103'])
            ->call('generateLedes')
            ->assertSet('step', 'preview') // Nao avanca para generate
            ->assertSee('future');
    }

    public function test_blocks_generation_when_fixed_fee_without_ff01(): void
    {
        $timekeeper = Timekeeper::factory()->create([
            'timekeeper_id_code' => 'CMR',
            'name' => 'RODRIGUES, CARLOS MAGNO',
            'classification' => 'PARTNR',
            'hourly_rate' => 300.00,
            'law_firm_id' => 'SF004554',
        ]);

        $matter = Matter::factory()->fixedFee()->create([
            'law_firm_matter_id' => 'LS-2026-24561',
            'open_date' => '2026-01-01',
        ]);

        Livewire::test(LedesConverter::class)
            ->set('step', 'preview')
            ->set('invoiceNumber', '4212')
            ->set('invoiceDate', '2026-03-01')
            ->set('totalAmount', 2400.00)
            ->set('billingStart', '2026-02-01')
            ->set('billingEnd', '2026-02-28')
            ->set('lawFirmMatterId', 'LS-2026-24561')
            ->set('matterId', $matter->id)
            ->set('timekeeperId', $timekeeper->id)
            ->set('lineItems', [
                ['description' => 'Legal services', 'amount' => 2400.00],
            ])
            ->set('taskCodes', ['L120']) // Deveria ser FF01
            ->set('activityCodes', ['A103'])
            ->call('generateLedes')
            ->assertSet('step', 'preview')
            ->assertSee('FF01');
    }

    public function test_shows_warnings_but_allows_generation(): void
    {
        $timekeeper = Timekeeper::factory()->create([
            'timekeeper_id_code' => 'CMR',
            'name' => 'RODRIGUES, CARLOS MAGNO',
            'classification' => 'PARTNR',
            'hourly_rate' => 300.00,
            'law_firm_id' => 'SF004554',
        ]);

        // Invoice date dentro do billing period, mas billing period > 90 dias atras
        Livewire::test(LedesConverter::class)
            ->set('step', 'preview')
            ->set('invoiceNumber', '4500')
            ->set('invoiceDate', '2025-10-15')
            ->set('totalAmount', 1000.00)
            ->set('billingStart', '2025-10-01')
            ->set('billingEnd', '2025-10-31') // >90 dias atras
            ->set('lawFirmMatterId', 'LS-TEST')
            ->set('timekeeperId', $timekeeper->id)
            ->set('lineItems', [
                ['description' => 'Legal services', 'amount' => 1000.00],
            ])
            ->set('taskCodes', ['L120'])
            ->set('activityCodes', ['A103'])
            ->call('generateLedes')
            ->assertSet('step', 'generate') // Avanca mesmo com warning
            ->assertSee('90');
    }

    public function test_displays_validation_errors_in_ui(): void
    {
        $timekeeper = Timekeeper::factory()->create([
            'timekeeper_id_code' => 'CMR',
            'name' => 'RODRIGUES, CARLOS MAGNO',
            'classification' => 'PARTNR',
            'hourly_rate' => 300.00,
            'law_firm_id' => 'SF004554',
        ]);

        Livewire::test(LedesConverter::class)
            ->set('step', 'preview')
            ->set('invoiceNumber', '4212')
            ->set('invoiceDate', '2026-03-11')
            ->set('totalAmount', 2400.00)
            ->set('billingStart', '2026-03-01')
            ->set('billingEnd', '2026-12-31')
            ->set('lawFirmMatterId', 'LS-2026')
            ->set('timekeeperId', $timekeeper->id)
            ->set('lineItems', [
                ['description' => 'Legal services', 'amount' => 2400.00],
            ])
            ->set('taskCodes', ['L120'])
            ->set('activityCodes', ['A103'])
            ->call('generateLedes')
            ->assertSee('Erros de Validacao');
    }

    // -------------------------------------------------------
    // Testes de selecao de matter
    // -------------------------------------------------------

    public function test_renders_matter_dropdown(): void
    {
        $matter = Matter::factory()->create([
            'law_firm_matter_id' => 'LS-2026-24561',
            'description' => 'Guilherme dos Santos Lima v. Salesforce',
        ]);

        Livewire::test(LedesConverter::class)
            ->assertSee('LS-2026-24561')
            ->assertSee('Guilherme dos Santos Lima v. Salesforce');
    }

    public function test_auto_selects_matter_by_matter_id_in_text(): void
    {
        $matter = Matter::factory()->create([
            'law_firm_matter_id' => 'LS-2026-24561',
            'description' => 'Guilherme dos Santos Lima v. Salesforce',
            'afa_type' => 'fixed_fee',
            'open_date' => '2026-03-06',
        ]);

        Timekeeper::factory()->create();

        Livewire::test(LedesConverter::class)
            ->set('rawText', $this->getSampleTextWithMatterId())
            ->call('parseText')
            ->assertSet('matterId', $matter->id)
            ->assertSet('lawFirmMatterId', 'LS-2026-24561');
    }

    public function test_manual_matter_selection_prefills_fields(): void
    {
        $matter = Matter::factory()->create([
            'law_firm_matter_id' => 'LS-2025-22672',
            'client_matter_id' => 'LS-2025-22672',
            'description' => 'General Employment Advice',
            'afa_type' => 'fixed_fee',
            'open_date' => '2026-01-15',
        ]);

        Livewire::test(LedesConverter::class)
            ->call('selectMatter', $matter->id)
            ->assertSet('matterId', $matter->id)
            ->assertSet('lawFirmMatterId', 'LS-2025-22672')
            ->assertSet('clientMatterId', 'LS-2025-22672')
            ->assertSet('matterDescription', 'General Employment Advice');
    }

    public function test_manual_selection_overrides_auto_detection(): void
    {
        $matterAuto = Matter::factory()->create([
            'law_firm_matter_id' => 'LS-2026-24561',
            'description' => 'Matter Auto',
        ]);

        $matterManual = Matter::factory()->create([
            'law_firm_matter_id' => 'LS-2025-22672',
            'description' => 'Matter Manual',
        ]);

        Timekeeper::factory()->create();

        Livewire::test(LedesConverter::class)
            ->set('rawText', $this->getSampleTextWithMatterId())
            ->call('parseText')
            ->assertSet('matterId', $matterAuto->id) // auto-detectou
            ->call('selectMatter', $matterManual->id)
            ->assertSet('matterId', $matterManual->id) // manual prevalece
            ->assertSet('lawFirmMatterId', 'LS-2025-22672');
    }

    public function test_detects_new_matter_id_not_in_database(): void
    {
        Timekeeper::factory()->create();

        Livewire::test(LedesConverter::class)
            ->set('rawText', $this->getSampleTextWithMatterId())
            ->call('parseText')
            ->assertSet('detectedNewMatterId', 'LS-2026-24561')
            ->assertSee('Novo matter detectado');
    }

    public function test_saves_new_matter_from_detected_data(): void
    {
        Timekeeper::factory()->create();

        Livewire::test(LedesConverter::class)
            ->set('rawText', $this->getSampleTextWithMatterId())
            ->call('parseText')
            ->call('saveNewMatter')
            ->assertSet('detectedNewMatterId', null);

        $this->assertDatabaseHas('matters', [
            'law_firm_matter_id' => 'LS-2026-24561',
            'description' => 'Guilherme dos Santos Lima v. Salesforce',
        ]);
    }

    public function test_clear_matter_selection(): void
    {
        $matter = Matter::factory()->create([
            'law_firm_matter_id' => 'LS-2025-22672',
            'description' => 'General Employment Advice',
        ]);

        Livewire::test(LedesConverter::class)
            ->call('selectMatter', $matter->id)
            ->assertSet('matterId', $matter->id)
            ->call('clearMatter')
            ->assertSet('matterId', null)
            ->assertSet('lawFirmMatterId', '');
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
}

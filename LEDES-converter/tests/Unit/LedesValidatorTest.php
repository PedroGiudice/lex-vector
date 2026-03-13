<?php

namespace Tests\Unit;

use App\Contracts\LedesValidatorInterface;
use App\Services\LedesValidator;
use Carbon\Carbon;
use PHPUnit\Framework\TestCase;

class LedesValidatorTest extends TestCase
{
    private LedesValidatorInterface $validator;

    protected function setUp(): void
    {
        parent::setUp();
        $this->validator = new LedesValidator;
    }

    // -------------------------------------------------------
    // Regra 1: BILLING_END_DATE nao pode ser data futura
    // -------------------------------------------------------

    public function test_rejects_future_billing_end_date(): void
    {
        $data = $this->getValidData();
        $data['billing_end'] = Carbon::tomorrow()->format('Y-m-d');

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['errors']);
        $this->assertStringContainsString('future', $result['errors'][0]);
    }

    public function test_accepts_today_as_billing_end_date(): void
    {
        $data = $this->getValidData();
        $data['billing_end'] = Carbon::today()->format('Y-m-d');
        $data['billing_start'] = Carbon::today()->subDays(30)->format('Y-m-d');
        $data['line_items'][0]['line_item_date'] = Carbon::today()->format('Y-m-d');

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['errors']);
    }

    public function test_accepts_past_billing_end_date(): void
    {
        $data = $this->getValidData();
        $data['billing_end'] = '2026-02-28';
        $data['billing_start'] = '2026-02-01';
        $data['line_items'][0]['line_item_date'] = '2026-02-15';

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['errors']);
    }

    // -------------------------------------------------------
    // Regra 2: LINE_ITEM_DATE >= data de abertura do matter
    // -------------------------------------------------------

    public function test_rejects_line_item_date_before_matter_open_date(): void
    {
        $data = $this->getValidData();
        $data['matter_open_date'] = '2026-03-06';
        $data['line_items'][0]['line_item_date'] = '2026-03-05';

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['errors']);
        $this->assertStringContainsString('abertura', $result['errors'][0]);
    }

    public function test_accepts_line_item_date_equal_to_open_date(): void
    {
        $data = $this->getValidData();
        $data['matter_open_date'] = '2026-02-01';
        $data['billing_start'] = '2026-02-01';
        $data['billing_end'] = '2026-02-28';
        $data['line_items'][0]['line_item_date'] = '2026-02-01';

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['errors']);
    }

    public function test_skips_open_date_check_when_null(): void
    {
        $data = $this->getValidData();
        $data['matter_open_date'] = null;

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['errors']);
    }

    // -------------------------------------------------------
    // Regra 3: LINE_ITEM_DATE dentro do billing period
    // -------------------------------------------------------

    public function test_rejects_line_item_date_before_billing_start(): void
    {
        $data = $this->getValidData();
        $data['billing_start'] = '2026-02-01';
        $data['billing_end'] = '2026-02-28';
        $data['line_items'][0]['line_item_date'] = '2026-01-31';

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['errors']);
        $this->assertStringContainsString('billing', strtolower($result['errors'][0]));
    }

    public function test_rejects_line_item_date_after_billing_end(): void
    {
        $data = $this->getValidData();
        $data['billing_start'] = '2026-02-01';
        $data['billing_end'] = '2026-02-28';
        $data['line_items'][0]['line_item_date'] = '2026-03-01';

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['errors']);
        $this->assertStringContainsString('billing', strtolower($result['errors'][0]));
    }

    public function test_accepts_line_item_date_at_billing_boundaries(): void
    {
        $data = $this->getValidData();
        $data['billing_start'] = '2026-02-01';
        $data['billing_end'] = '2026-02-28';
        $data['line_items'][0]['line_item_date'] = '2026-02-01';

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['errors']);
    }

    // -------------------------------------------------------
    // Regra 4: Fixed Fee AFA exige task code FF01
    // -------------------------------------------------------

    public function test_rejects_non_ff01_task_code_for_fixed_fee(): void
    {
        $data = $this->getValidData();
        $data['afa_type'] = 'fixed_fee';
        $data['line_items'][0]['task_code'] = 'L120';

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['errors']);
        $this->assertStringContainsString('FF01', $result['errors'][0]);
    }

    public function test_rejects_non_ff01_task_code_for_scheduled_fixed_fee(): void
    {
        $data = $this->getValidData();
        $data['afa_type'] = 'scheduled_fixed_fee';
        $data['line_items'][0]['task_code'] = 'L110';

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['errors']);
        $this->assertStringContainsString('FF01', $result['errors'][0]);
    }

    public function test_accepts_ff01_task_code_for_fixed_fee(): void
    {
        $data = $this->getValidData();
        $data['afa_type'] = 'fixed_fee';
        $data['line_items'][0]['task_code'] = 'FF01';

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['errors']);
    }

    public function test_accepts_any_task_code_for_hourly(): void
    {
        $data = $this->getValidData();
        $data['afa_type'] = 'hourly';
        $data['line_items'][0]['task_code'] = 'L120';

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['errors']);
    }

    // -------------------------------------------------------
    // Regra 5: Warning para invoice > 90 dias apos billing end
    // -------------------------------------------------------

    public function test_warns_when_invoice_submitted_after_90_days(): void
    {
        $data = $this->getValidData();
        $data['billing_end'] = '2025-11-30';
        $data['billing_start'] = '2025-11-01';
        $data['line_items'][0]['line_item_date'] = '2025-11-15';
        // "Hoje" sera > 90 dias apos 2025-11-30

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['warnings']);
        $this->assertStringContainsString('90', $result['warnings'][0]);
    }

    public function test_no_warning_when_within_90_days(): void
    {
        $data = $this->getValidData();
        // Usar datas recentes para garantir que estamos dentro de 90 dias
        $data['billing_end'] = Carbon::today()->subDays(30)->format('Y-m-d');
        $data['billing_start'] = Carbon::today()->subDays(60)->format('Y-m-d');
        $data['line_items'][0]['line_item_date'] = Carbon::today()->subDays(45)->format('Y-m-d');

        $result = $this->validator->validate($data);

        $this->assertEmpty($result['warnings']);
    }

    // -------------------------------------------------------
    // Regra 6: Warning accruals ate dia 27
    // -------------------------------------------------------

    public function test_warns_about_accrual_deadline_after_day_27(): void
    {
        $data = $this->getValidData();

        // Forcar "hoje" como dia 28 para testar
        $result = $this->validator->validate($data, Carbon::create(2026, 3, 28));

        $this->assertNotEmpty($result['warnings']);
        $this->assertStringContainsString('accrual', strtolower($result['warnings'][0]));
    }

    public function test_no_accrual_warning_before_day_27(): void
    {
        $data = $this->getValidData();

        $result = $this->validator->validate($data, Carbon::create(2026, 3, 15));

        // Pode ter warnings de 90 dias, mas nao de accrual
        $accrualWarnings = array_filter(
            $result['warnings'],
            fn (string $w): bool => str_contains(strtolower($w), 'accrual')
        );

        $this->assertEmpty($accrualWarnings);
    }

    // -------------------------------------------------------
    // Multiplos line items
    // -------------------------------------------------------

    public function test_validates_all_line_items_independently(): void
    {
        $data = $this->getValidData();
        $data['line_items'][] = [
            'line_item_date' => '2026-01-15', // Fora do billing period
            'task_code' => 'L120',
            'activity_code' => 'A103',
            'description' => 'Segundo item',
            'amount' => 500.00,
        ];

        $result = $this->validator->validate($data);

        $this->assertNotEmpty($result['errors']);
    }

    // -------------------------------------------------------
    // Resultado estruturado
    // -------------------------------------------------------

    public function test_returns_errors_and_warnings_arrays(): void
    {
        $data = $this->getValidData();

        $result = $this->validator->validate($data);

        $this->assertArrayHasKey('errors', $result);
        $this->assertArrayHasKey('warnings', $result);
        $this->assertIsArray($result['errors']);
        $this->assertIsArray($result['warnings']);
    }

    /**
     * Retorna dados validos (sem erros nem warnings quando executado em data razoavel).
     *
     * @return array<string, mixed>
     */
    private function getValidData(): array
    {
        return [
            'billing_start' => '2026-02-01',
            'billing_end' => '2026-02-28',
            'invoice_date' => '2026-03-01',
            'afa_type' => 'hourly',
            'matter_open_date' => '2025-01-01',
            'line_items' => [
                [
                    'line_item_date' => '2026-02-15',
                    'task_code' => 'L120',
                    'activity_code' => 'A103',
                    'description' => 'Legal services rendered',
                    'amount' => 2400.00,
                ],
            ],
        ];
    }
}

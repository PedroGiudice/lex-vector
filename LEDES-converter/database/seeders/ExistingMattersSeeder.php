<?php

namespace Database\Seeders;

use App\Models\Client;
use App\Models\Invoice;
use App\Models\InvoiceLineItem;
use App\Models\Matter;
use App\Models\Timekeeper;
use Illuminate\Database\Seeder;

class ExistingMattersSeeder extends Seeder
{
    /**
     * Popula matters e invoices historicos extraidos dos arquivos LEDES existentes.
     *
     * Fontes: /legal-workbench/invoices-salesforce/output/manual/*.ledes
     */
    public function run(): void
    {
        $client = Client::query()->where('name', 'Salesforce, Inc.')->firstOrFail();
        $timekeeper = Timekeeper::query()->where('timekeeper_id_code', 'CMR')->firstOrFail();

        // Matter 1: General Employment Advice
        $matter1 = Matter::query()->updateOrCreate(
            ['law_firm_matter_id' => 'LS-2025-22672'],
            [
                'client_id' => $client->id,
                'matter_number' => 'LS-2025-22672',
                'client_matter_id' => 'LS-2025-22672',
                'description' => 'General Employment Advice',
                'afa_type' => 'fixed_fee',
                'open_date' => null,
            ]
        );

        // Matter 2: Guilherme dos Santos Lima v. Salesforce
        $matter2 = Matter::query()->updateOrCreate(
            ['law_firm_matter_id' => 'LS-2026-24561'],
            [
                'client_id' => $client->id,
                'matter_number' => 'LS-2026-24561',
                'client_matter_id' => 'LS-2026-24561',
                'description' => 'Guilherme dos Santos Lima v. Salesforce',
                'afa_type' => 'fixed_fee',
                'open_date' => '2026-03-06',
            ]
        );

        // Invoices do Matter 1 (General Employment Advice)
        $invoicesData = [
            [
                'invoice_number' => '4170',
                'invoice_date' => '2026-02-03',
                'billing_start' => '2025-09-01',
                'billing_end' => '2025-09-30',
                'total' => 2000.00,
                'description' => 'General Employment Advice - September 2025',
                'line_item_date' => '2025-09-15',
                'line_item_description' => 'Provide general legal advice for September 2025',
            ],
            [
                'invoice_number' => '4171',
                'invoice_date' => '2026-02-03',
                'billing_start' => '2025-10-01',
                'billing_end' => '2025-10-31',
                'total' => 2000.00,
                'description' => 'General Employment Advice - October 2025',
                'line_item_date' => '2025-10-15',
                'line_item_description' => 'Provide general legal advice for October 2025',
            ],
            [
                'invoice_number' => '4172',
                'invoice_date' => '2026-02-03',
                'billing_start' => '2025-11-01',
                'billing_end' => '2025-11-30',
                'total' => 2000.00,
                'description' => 'General Employment Advice - November 2025',
                'line_item_date' => '2025-11-15',
                'line_item_description' => 'Provide general legal advice for November 2025',
            ],
            [
                'invoice_number' => '4173',
                'invoice_date' => '2026-02-03',
                'billing_start' => '2025-12-01',
                'billing_end' => '2025-12-31',
                'total' => 2000.00,
                'description' => 'General Employment Advice - December 2025',
                'line_item_date' => '2025-12-15',
                'line_item_description' => 'Provide general legal advice for December 2025',
            ],
            [
                'invoice_number' => '4174',
                'invoice_date' => '2026-02-03',
                'billing_start' => '2026-01-01',
                'billing_end' => '2026-01-31',
                'total' => 2000.00,
                'description' => 'General Employment Advice - January 2026',
                'line_item_date' => '2026-01-15',
                'line_item_description' => 'Provide general legal advice for January 2026',
            ],
        ];

        foreach ($invoicesData as $data) {
            $this->createInvoiceWithLineItem(
                matter: $matter1,
                timekeeper: $timekeeper,
                data: $data,
                taskCode: 'L110',
                activityCode: 'A106',
                units: 6.67,
                unitCost: 300.00,
            );
        }

        // Invoice do Matter 2 (Guilherme dos Santos Lima v. Salesforce)
        $this->createInvoiceWithLineItem(
            matter: $matter2,
            timekeeper: $timekeeper,
            data: [
                'invoice_number' => '4212',
                'invoice_date' => '2026-03-11',
                'billing_start' => '2026-03-01',
                'billing_end' => '2026-03-31',
                'total' => 2400.00,
                'description' => 'Guilherme dos Santos Lima v. Salesforce - March 2026',
                'line_item_date' => '2026-03-11',
                'line_item_description' => 'Draft and file a defense and appear in court for the hearing in which we reached a settlement',
            ],
            taskCode: 'L120',
            activityCode: 'A106',
            units: 8.00,
            unitCost: 300.00,
        );
    }

    /**
     * @param  array{invoice_number: string, invoice_date: string, billing_start: string, billing_end: string, total: float, description: string, line_item_date: string, line_item_description: string}  $data
     */
    private function createInvoiceWithLineItem(
        Matter $matter,
        Timekeeper $timekeeper,
        array $data,
        string $taskCode,
        string $activityCode,
        float $units,
        float $unitCost,
    ): void {
        $invoice = Invoice::query()->updateOrCreate(
            ['invoice_number' => $data['invoice_number']],
            [
                'matter_id' => $matter->id,
                'timekeeper_id' => $timekeeper->id,
                'invoice_date' => $data['invoice_date'],
                'billing_start' => $data['billing_start'],
                'billing_end' => $data['billing_end'],
                'total' => $data['total'],
                'description' => $data['description'],
            ]
        );

        InvoiceLineItem::query()->updateOrCreate(
            [
                'invoice_id' => $invoice->id,
                'line_number' => 1,
            ],
            [
                'fee_type' => 'F',
                'units' => $units,
                'unit_cost' => $unitCost,
                'adjustment_amount' => 0.00,
                'total' => $data['total'],
                'line_item_date' => $data['line_item_date'],
                'task_code' => $taskCode,
                'expense_code' => '',
                'activity_code' => $activityCode,
                'description' => $data['line_item_description'],
            ]
        );
    }
}

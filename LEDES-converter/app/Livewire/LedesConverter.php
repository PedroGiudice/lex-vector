<?php

namespace App\Livewire;

use App\Contracts\LedesGeneratorInterface;
use App\Contracts\LedesValidatorInterface;
use App\Contracts\TextParserInterface;
use App\Models\Client;
use App\Models\Invoice;
use App\Models\InvoiceLineItem;
use App\Models\Matter;
use App\Models\Timekeeper;
use App\Models\UtbmsActivityCode;
use App\Models\UtbmsTaskCode;
use Illuminate\Contracts\View\View;
use Illuminate\Support\Facades\DB;
use Livewire\Component;
use Symfony\Component\HttpFoundation\StreamedResponse;

class LedesConverter extends Component
{
    // Step tracking
    public string $step = 'input'; // input, preview, generate

    // Input
    public string $rawText = '';

    // Parsed data
    public ?string $clientName = null;

    public ?string $contactPerson = null;

    public ?string $invoiceNumber = null;

    public ?string $invoiceDate = null;

    public ?string $matterDescription = null;

    public ?float $totalAmount = null;

    /** @var array<int, array{description: string, amount: float}> */
    public array $lineItems = [];

    // Persistent selections
    public ?int $matterId = null;

    public ?int $timekeeperId = null;

    public string $lawFirmMatterId = '';

    public string $clientMatterId = '';

    public string $billingStart = '';

    public string $billingEnd = '';

    public string $invoiceDescription = '';

    // Line item UTBMS codes
    /** @var array<int, string> */
    public array $taskCodes = [];

    /** @var array<int, string> */
    public array $activityCodes = [];

    // Matter detection
    public ?string $detectedNewMatterId = null;

    public ?string $detectedNewMatterDescription = null;

    public ?string $detectedNewMatterClientName = null;

    public bool $manualMatterSelection = false;

    // Validation results
    /** @var array<int, string> */
    public array $validationErrors = [];

    /** @var array<int, string> */
    public array $validationWarnings = [];

    // Generated output
    public string $ledesOutput = '';

    public function parseText(): void
    {
        $this->validate([
            'rawText' => 'required|string|min:10',
        ]);

        /** @var TextParserInterface $parser */
        $parser = app(TextParserInterface::class);
        $parsed = $parser->parse($this->rawText);

        $this->clientName = $parsed['client_name'];
        $this->contactPerson = $parsed['contact_person'];
        $this->invoiceNumber = $parsed['invoice_number'];
        $this->invoiceDate = $parsed['invoice_date'];
        $this->matterDescription = $parsed['matter_description'];
        $this->totalAmount = $parsed['total_amount'];
        $this->lineItems = $parsed['line_items'];

        // Default billing period: first and last day of invoice month
        if ($this->invoiceDate) {
            $timestamp = strtotime($this->invoiceDate);
            if ($timestamp !== false) {
                $this->billingStart = date('Y-m-01', $timestamp);
                $this->billingEnd = date('Y-m-t', $timestamp);
            }
        }

        $this->invoiceDescription = ($this->matterDescription ?? '').
            ($this->invoiceDate ? ' - '.date('F Y', strtotime($this->invoiceDate)) : '');

        // Default UTBMS codes for each line item
        foreach ($this->lineItems as $index => $item) {
            $this->taskCodes[$index] = $this->taskCodes[$index] ?? 'L120';
            $this->activityCodes[$index] = $this->activityCodes[$index] ?? 'A103';
        }

        // Auto-select first timekeeper
        $firstTimekeeper = Timekeeper::query()->first();
        if ($firstTimekeeper) {
            $this->timekeeperId = $firstTimekeeper->id;
        }

        // Reset detected new matter
        $this->detectedNewMatterId = null;
        $this->detectedNewMatterDescription = null;
        $this->detectedNewMatterClientName = null;

        // Auto-detect matter: primeiro por matter_id, depois por description
        if (! $this->manualMatterSelection) {
            $matterId = $parsed['matter_id'] ?? null;
            $matter = null;

            if ($matterId) {
                $matter = Matter::query()
                    ->where('law_firm_matter_id', $matterId)
                    ->first();

                if (! $matter) {
                    // Matter ID encontrado no texto mas nao existe no banco
                    $this->detectedNewMatterId = $matterId;
                    $this->detectedNewMatterDescription = $this->matterDescription;
                    $this->detectedNewMatterClientName = $this->clientName;
                }
            }

            if (! $matter && ! $matterId && $this->matterDescription) {
                $matter = Matter::query()
                    ->where('description', 'like', '%'.$this->matterDescription.'%')
                    ->first();
            }

            if ($matter) {
                $this->applyMatterData($matter);
            }
        }

        $this->step = 'preview';
    }

    public function generateLedes(): void
    {
        $this->validate([
            'invoiceNumber' => 'required|string',
            'invoiceDate' => 'required|date',
            'totalAmount' => 'required|numeric|min:0.01',
            'billingStart' => 'required|date',
            'billingEnd' => 'required|date',
            'timekeeperId' => 'required|exists:timekeepers,id',
            'lawFirmMatterId' => 'required|string',
        ]);

        // Buscar matter para obter afa_type e open_date
        $matter = $this->matterId ? Matter::query()->find($this->matterId) : null;

        $lineItemsData = [];
        foreach ($this->lineItems as $index => $item) {
            $lineItemsData[] = [
                'description' => $item['description'],
                'amount' => $item['amount'],
                'task_code' => $this->taskCodes[$index] ?? 'L120',
                'activity_code' => $this->activityCodes[$index] ?? 'A103',
                'line_item_date' => $this->invoiceDate,
            ];
        }

        // Validar regras de negocio LEDES
        $validationData = [
            'billing_start' => $this->billingStart,
            'billing_end' => $this->billingEnd,
            'invoice_date' => $this->invoiceDate,
            'afa_type' => $matter?->afa_type ?? 'hourly',
            'matter_open_date' => $matter?->open_date?->format('Y-m-d'),
            'line_items' => $lineItemsData,
        ];

        /** @var LedesValidatorInterface $validator */
        $validator = app(LedesValidatorInterface::class);
        $result = $validator->validate($validationData);

        $this->validationErrors = $result['errors'];
        $this->validationWarnings = $result['warnings'];

        // Se houver erros, nao gerar o LEDES
        if (! empty($result['errors'])) {
            return;
        }

        /** @var Timekeeper $timekeeper */
        $timekeeper = Timekeeper::query()->findOrFail($this->timekeeperId);

        $data = [
            'invoice_date' => $this->invoiceDate,
            'invoice_number' => $this->invoiceNumber,
            'client_id' => $this->clientName ?? '',
            'law_firm_matter_id' => $this->lawFirmMatterId,
            'client_matter_id' => $this->clientMatterId,
            'total' => $this->totalAmount,
            'billing_start' => $this->billingStart,
            'billing_end' => $this->billingEnd,
            'invoice_description' => $this->invoiceDescription,
            'timekeeper_id' => $timekeeper->timekeeper_id_code,
            'timekeeper_name' => $timekeeper->name,
            'timekeeper_classification' => $timekeeper->classification,
            'law_firm_id' => $timekeeper->law_firm_id,
            'unit_cost' => $timekeeper->hourly_rate,
            'line_items' => $lineItemsData,
        ];

        /** @var LedesGeneratorInterface $generator */
        $generator = app(LedesGeneratorInterface::class);
        $this->ledesOutput = $generator->generate($data);

        // Persistir invoice no historico
        $this->persistInvoice($timekeeper);

        $this->step = 'generate';
    }

    public function selectMatter(int $id): void
    {
        $matter = Matter::query()->with('client')->find($id);
        if (! $matter) {
            return;
        }

        $this->manualMatterSelection = true;
        $this->detectedNewMatterId = null;
        $this->applyMatterData($matter);
    }

    public function clearMatter(): void
    {
        $this->matterId = null;
        $this->lawFirmMatterId = '';
        $this->clientMatterId = '';
        $this->matterDescription = null;
        $this->manualMatterSelection = false;
        $this->detectedNewMatterId = null;
        $this->detectedNewMatterDescription = null;
        $this->detectedNewMatterClientName = null;
    }

    public function saveNewMatter(): void
    {
        if (! $this->detectedNewMatterId) {
            return;
        }

        $client = Client::query()->firstOrCreate(
            ['name' => $this->detectedNewMatterClientName ?? $this->clientName ?? 'Unknown'],
            ['contact_person' => $this->contactPerson]
        );

        $matter = Matter::query()->create([
            'client_id' => $client->id,
            'matter_number' => $this->detectedNewMatterId,
            'law_firm_matter_id' => $this->detectedNewMatterId,
            'client_matter_id' => $this->detectedNewMatterId,
            'description' => $this->detectedNewMatterDescription ?? $this->matterDescription ?? '',
            'afa_type' => 'hourly',
            'open_date' => null,
        ]);

        $this->detectedNewMatterId = null;
        $this->detectedNewMatterDescription = null;
        $this->detectedNewMatterClientName = null;

        $this->applyMatterData($matter);
    }

    private function applyMatterData(Matter $matter): void
    {
        $this->matterId = $matter->id;
        $this->lawFirmMatterId = $matter->law_firm_matter_id;
        $this->clientMatterId = $matter->client_matter_id ?? '';
        $this->matterDescription = $matter->description;

        if ($matter->relationLoaded('client') && $matter->client) {
            $this->clientName = $matter->client->name;
        }
    }

    public function downloadLedes(): StreamedResponse
    {
        $filename = sprintf('invoice_%s_%s.ledes',
            $this->invoiceNumber ?? 'unknown',
            date('Ymd')
        );

        return response()->streamDownload(function (): void {
            echo $this->ledesOutput;
        }, $filename, [
            'Content-Type' => 'text/plain',
        ]);
    }

    public function reset_form(): void
    {
        $this->reset();
        $this->step = 'input';
    }

    public function render(): View
    {
        return view('livewire.ledes-converter', [
            'matters' => Matter::query()->with('client')->get(),
            'timekeepers' => Timekeeper::all(),
            'utbmsTaskCodes' => UtbmsTaskCode::all(),
            'utbmsActivityCodes' => UtbmsActivityCode::all(),
            'recentInvoices' => Invoice::query()
                ->with(['matter.client', 'timekeeper'])
                ->latest()
                ->take(10)
                ->get(),
        ]);
    }

    private function persistInvoice(Timekeeper $timekeeper): void
    {
        DB::transaction(function () use ($timekeeper): void {
            // Criar ou encontrar matter se necessario
            $matter = null;
            if ($this->matterId) {
                $matter = Matter::query()->find($this->matterId);
            }

            if (! $matter && $this->lawFirmMatterId) {
                $client = Client::query()->firstOrCreate(
                    ['name' => $this->clientName ?? 'Unknown'],
                    ['contact_person' => $this->contactPerson]
                );

                $matter = Matter::query()->create([
                    'client_id' => $client->id,
                    'matter_number' => $this->lawFirmMatterId,
                    'law_firm_matter_id' => $this->lawFirmMatterId,
                    'client_matter_id' => $this->clientMatterId ?: null,
                    'description' => $this->matterDescription ?? '',
                ]);

                $this->matterId = $matter->id;
            }

            if (! $matter) {
                return;
            }

            $invoice = Invoice::query()->create([
                'matter_id' => $matter->id,
                'timekeeper_id' => $timekeeper->id,
                'invoice_number' => $this->invoiceNumber ?? '',
                'invoice_date' => $this->invoiceDate,
                'billing_start' => $this->billingStart,
                'billing_end' => $this->billingEnd,
                'total' => $this->totalAmount ?? 0,
                'description' => $this->invoiceDescription,
                'ledes_content' => $this->ledesOutput,
            ]);

            foreach ($this->lineItems as $index => $item) {
                InvoiceLineItem::query()->create([
                    'invoice_id' => $invoice->id,
                    'line_number' => $index + 1,
                    'fee_type' => 'F',
                    'units' => $timekeeper->hourly_rate > 0
                        ? round($item['amount'] / $timekeeper->hourly_rate, 2)
                        : 0,
                    'unit_cost' => $timekeeper->hourly_rate,
                    'total' => $item['amount'],
                    'line_item_date' => $this->invoiceDate,
                    'task_code' => $this->taskCodes[$index] ?? 'L120',
                    'activity_code' => $this->activityCodes[$index] ?? 'A103',
                    'description' => $item['description'],
                ]);
            }
        });
    }
}

<div class="space-y-6">

    {{-- Selecao de Matter (visivel em input e preview) --}}
    @if ($step === 'input' || $step === 'preview')
        <div class="rounded-lg border border-gray-200 bg-white p-6">
            <h2 class="mb-3 text-base font-semibold">Matter</h2>

            @if ($matterId)
                {{-- Matter selecionado --}}
                @php $selectedMatter = $matters->firstWhere('id', $matterId); @endphp
                @if ($selectedMatter)
                    <div class="flex items-start justify-between rounded border border-blue-200 bg-blue-50 p-3">
                        <div>
                            <p class="text-sm font-medium text-blue-900">{{ $selectedMatter->law_firm_matter_id }}</p>
                            <p class="text-sm text-blue-800">{{ $selectedMatter->description }}</p>
                            <p class="mt-1 text-xs text-blue-600">
                                Cliente: {{ $selectedMatter->client->name ?? '-' }}
                                | AFA: {{ $selectedMatter->afa_type }}
                                @if ($selectedMatter->open_date)
                                    | Abertura: {{ $selectedMatter->open_date->format('d/m/Y') }}
                                @endif
                            </p>
                        </div>
                        <button
                            wire:click="clearMatter"
                            class="ml-3 text-sm text-blue-600 hover:text-blue-800"
                        >Limpar</button>
                    </div>
                @endif
            @else
                {{-- Dropdown de selecao --}}
                <select
                    wire:change="selectMatter($event.target.value)"
                    class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                >
                    <option value="">Selecionar matter...</option>
                    @foreach ($matters as $m)
                        <option value="{{ $m->id }}">
                            {{ $m->law_firm_matter_id }} - {{ $m->description }}
                            ({{ $m->client->name ?? '-' }})
                        </option>
                    @endforeach
                </select>
            @endif

            {{-- Novo matter detectado --}}
            @if ($detectedNewMatterId)
                <div class="mt-3 rounded border border-yellow-300 bg-yellow-50 p-3">
                    <p class="text-sm font-medium text-yellow-800">
                        Novo matter detectado: {{ $detectedNewMatterId }}
                    </p>
                    @if ($detectedNewMatterDescription)
                        <p class="text-sm text-yellow-700">{{ $detectedNewMatterDescription }}</p>
                    @endif
                    <button
                        wire:click="saveNewMatter"
                        class="mt-2 rounded bg-yellow-600 px-3 py-1 text-sm font-medium text-white hover:bg-yellow-700"
                    >
                        Salvar Matter
                    </button>
                </div>
            @endif
        </div>
    @endif

    {{-- Step 1: Input --}}
    @if ($step === 'input')
        <div class="rounded-lg border border-gray-200 bg-white p-6">
            <h2 class="mb-4 text-base font-semibold">Colar Texto do Statement</h2>
            <p class="mb-4 text-sm text-gray-500">
                Cole o texto do statement recebido do cliente. O sistema extraira automaticamente os dados.
            </p>

            <form wire:submit="parseText">
                <textarea
                    wire:model="rawText"
                    rows="12"
                    class="w-full rounded border border-gray-300 p-3 font-mono text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    placeholder="CLIENT: SALESFORCE.COM, INC.&#10;50 Freemont St. Suite 300&#10;San Francisco CA USA 94105 2231&#10;Date of Issuance: March 11, 2026&#10;..."
                ></textarea>

                @error('rawText')
                    <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
                @enderror

                <button
                    type="submit"
                    class="mt-4 rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                    Extrair Dados
                </button>
            </form>
        </div>

        {{-- Historico recente --}}
        @if ($recentInvoices->isNotEmpty())
            <div class="rounded-lg border border-gray-200 bg-white p-6">
                <h2 class="mb-4 text-base font-semibold">Invoices Recentes</h2>
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b text-left text-gray-500">
                            <th class="pb-2">#</th>
                            <th class="pb-2">Cliente</th>
                            <th class="pb-2">Matter</th>
                            <th class="pb-2">Valor</th>
                            <th class="pb-2">Data</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach ($recentInvoices as $inv)
                            <tr class="border-b border-gray-100">
                                <td class="py-2">{{ $inv->invoice_number }}</td>
                                <td class="py-2">{{ $inv->matter->client->name ?? '-' }}</td>
                                <td class="py-2 truncate max-w-[200px]">{{ $inv->matter->description ?? '-' }}</td>
                                <td class="py-2">US ${{ number_format($inv->total, 2) }}</td>
                                <td class="py-2">{{ $inv->invoice_date->format('d/m/Y') }}</td>
                            </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
        @endif
    @endif

    {{-- Step 2: Preview --}}
    @if ($step === 'preview')
        <div class="rounded-lg border border-gray-200 bg-white p-6">
            <div class="mb-4 flex items-center justify-between">
                <h2 class="text-base font-semibold">Dados Extraidos</h2>
                <button
                    wire:click="$set('step', 'input')"
                    class="text-sm text-gray-500 hover:text-gray-700"
                >
                    Voltar
                </button>
            </div>

            <form wire:submit="generateLedes" class="space-y-6">
                {{-- Dados basicos --}}
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Cliente</label>
                        <input type="text" wire:model="clientName"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                    </div>
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Contato</label>
                        <input type="text" wire:model="contactPerson"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                    </div>
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Invoice #</label>
                        <input type="text" wire:model="invoiceNumber"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                        @error('invoiceNumber') <p class="text-xs text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Data Invoice</label>
                        <input type="date" wire:model="invoiceDate"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                        @error('invoiceDate') <p class="text-xs text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Valor Total</label>
                        <input type="number" step="0.01" wire:model="totalAmount"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                        @error('totalAmount') <p class="text-xs text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Matter</label>
                        <input type="text" wire:model="matterDescription"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                    </div>
                </div>

                {{-- Billing period --}}
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Billing Start</label>
                        <input type="date" wire:model="billingStart"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                        @error('billingStart') <p class="text-xs text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Billing End</label>
                        <input type="date" wire:model="billingEnd"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                        @error('billingEnd') <p class="text-xs text-red-600">{{ $message }}</p> @enderror
                    </div>
                </div>

                {{-- Matter IDs --}}
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Law Firm Matter ID</label>
                        <input type="text" wire:model="lawFirmMatterId"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                        @error('lawFirmMatterId') <p class="text-xs text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label class="mb-1 block text-sm font-medium text-gray-700">Client Matter ID</label>
                        <input type="text" wire:model="clientMatterId"
                            class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                    </div>
                </div>

                {{-- Invoice description --}}
                <div>
                    <label class="mb-1 block text-sm font-medium text-gray-700">Invoice Description</label>
                    <input type="text" wire:model="invoiceDescription"
                        class="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
                </div>

                {{-- Timekeeper --}}
                <div>
                    <label class="mb-1 block text-sm font-medium text-gray-700">Timekeeper</label>
                    <select wire:model="timekeeperId"
                        class="w-full rounded border border-gray-300 px-3 py-2 text-sm">
                        <option value="">Selecionar...</option>
                        @foreach ($timekeepers as $tk)
                            <option value="{{ $tk->id }}">
                                {{ $tk->name }} ({{ $tk->timekeeper_id_code }}) - US ${{ $tk->hourly_rate }}/h
                            </option>
                        @endforeach
                    </select>
                    @error('timekeeperId') <p class="text-xs text-red-600">{{ $message }}</p> @enderror
                </div>

                {{-- Line Items --}}
                <div>
                    <h3 class="mb-2 text-sm font-semibold">Line Items</h3>
                    @foreach ($lineItems as $index => $item)
                        <div class="mb-3 rounded border border-gray-100 bg-gray-50 p-3">
                            <div class="mb-2">
                                <label class="mb-1 block text-xs text-gray-500">Descricao</label>
                                <textarea
                                    wire:model="lineItems.{{ $index }}.description"
                                    rows="2"
                                    class="w-full rounded border border-gray-200 px-2 py-1 text-sm"
                                ></textarea>
                            </div>
                            <div class="grid grid-cols-3 gap-3">
                                <div>
                                    <label class="mb-1 block text-xs text-gray-500">Valor (US$)</label>
                                    <input type="number" step="0.01"
                                        wire:model="lineItems.{{ $index }}.amount"
                                        class="w-full rounded border border-gray-200 px-2 py-1 text-sm" />
                                </div>
                                <div>
                                    <label class="mb-1 block text-xs text-gray-500">Task Code</label>
                                    <select wire:model="taskCodes.{{ $index }}"
                                        class="w-full rounded border border-gray-200 px-2 py-1 text-sm">
                                        @foreach ($utbmsTaskCodes as $code)
                                            <option value="{{ $code->code }}">
                                                {{ $code->code }} - {{ $code->description }}
                                            </option>
                                        @endforeach
                                    </select>
                                </div>
                                <div>
                                    <label class="mb-1 block text-xs text-gray-500">Activity Code</label>
                                    <select wire:model="activityCodes.{{ $index }}"
                                        class="w-full rounded border border-gray-200 px-2 py-1 text-sm">
                                        @foreach ($utbmsActivityCodes as $code)
                                            <option value="{{ $code->code }}">
                                                {{ $code->code }} - {{ $code->description }}
                                            </option>
                                        @endforeach
                                    </select>
                                </div>
                            </div>
                        </div>
                    @endforeach
                </div>

                {{-- Validation Errors --}}
                @if (! empty($validationErrors))
                    <div class="rounded border border-red-300 bg-red-50 p-4">
                        <h4 class="mb-2 text-sm font-semibold text-red-800">Erros de Validacao (bloqueiam a geracao)</h4>
                        <ul class="list-inside list-disc space-y-1 text-sm text-red-700">
                            @foreach ($validationErrors as $error)
                                <li>{{ $error }}</li>
                            @endforeach
                        </ul>
                    </div>
                @endif

                {{-- Validation Warnings --}}
                @if (! empty($validationWarnings))
                    <div class="rounded border border-yellow-300 bg-yellow-50 p-4">
                        <h4 class="mb-2 text-sm font-semibold text-yellow-800">Avisos (nao bloqueiam, mas atencao)</h4>
                        <ul class="list-inside list-disc space-y-1 text-sm text-yellow-700">
                            @foreach ($validationWarnings as $warning)
                                <li>{{ $warning }}</li>
                            @endforeach
                        </ul>
                    </div>
                @endif

                <button
                    type="submit"
                    class="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                >
                    Gerar LEDES 1998B
                </button>
            </form>
        </div>
    @endif

    {{-- Step 3: Generated output --}}
    @if ($step === 'generate')
        <div class="rounded-lg border border-gray-200 bg-white p-6">
            <div class="mb-4 flex items-center justify-between">
                <h2 class="text-base font-semibold">LEDES 1998B Gerado</h2>
                <div class="flex gap-2">
                    <button
                        wire:click="downloadLedes"
                        class="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                    >
                        Baixar Arquivo
                    </button>
                    <button
                        wire:click="reset_form"
                        class="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                        Nova Conversao
                    </button>
                </div>
            </div>

            <pre class="overflow-x-auto rounded bg-gray-900 p-4 text-xs text-green-400"><code>{{ $ledesOutput }}</code></pre>

            <div class="mt-4 rounded bg-green-50 p-3 text-sm text-green-800">
                Invoice #{{ $invoiceNumber }} salva no historico. Arquivo pronto para download.
            </div>
        </div>
    @endif
</div>

<?php

namespace App\Models;

use Database\Factories\InvoiceLineItemFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class InvoiceLineItem extends Model
{
    /** @use HasFactory<InvoiceLineItemFactory> */
    use HasFactory;

    protected $fillable = [
        'invoice_id',
        'line_number',
        'fee_type',
        'units',
        'unit_cost',
        'adjustment_amount',
        'total',
        'line_item_date',
        'task_code',
        'expense_code',
        'activity_code',
        'description',
    ];

    /** @return array<string, string> */
    protected function casts(): array
    {
        return [
            'units' => 'decimal:2',
            'unit_cost' => 'decimal:2',
            'adjustment_amount' => 'decimal:2',
            'total' => 'decimal:2',
            'line_item_date' => 'date',
        ];
    }

    /** @return BelongsTo<Invoice, $this> */
    public function invoice(): BelongsTo
    {
        return $this->belongsTo(Invoice::class);
    }
}

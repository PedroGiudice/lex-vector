<?php

namespace App\Models;

use Database\Factories\InvoiceFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Invoice extends Model
{
    /** @use HasFactory<InvoiceFactory> */
    use HasFactory;

    protected $fillable = [
        'matter_id',
        'timekeeper_id',
        'invoice_number',
        'invoice_date',
        'billing_start',
        'billing_end',
        'total',
        'description',
        'ledes_content',
    ];

    /** @return array<string, string> */
    protected function casts(): array
    {
        return [
            'invoice_date' => 'date',
            'billing_start' => 'date',
            'billing_end' => 'date',
            'total' => 'decimal:2',
        ];
    }

    /** @return BelongsTo<Matter, $this> */
    public function matter(): BelongsTo
    {
        return $this->belongsTo(Matter::class);
    }

    /** @return BelongsTo<Timekeeper, $this> */
    public function timekeeper(): BelongsTo
    {
        return $this->belongsTo(Timekeeper::class);
    }

    /** @return HasMany<InvoiceLineItem, $this> */
    public function lineItems(): HasMany
    {
        return $this->hasMany(InvoiceLineItem::class);
    }
}

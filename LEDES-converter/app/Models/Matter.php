<?php

namespace App\Models;

use Database\Factories\MatterFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Matter extends Model
{
    /** @use HasFactory<MatterFactory> */
    use HasFactory;

    protected $fillable = [
        'client_id',
        'matter_number',
        'law_firm_matter_id',
        'client_matter_id',
        'description',
        'afa_type',
        'open_date',
    ];

    /** @return array<string, string> */
    protected function casts(): array
    {
        return [
            'open_date' => 'date',
        ];
    }

    /** @return BelongsTo<Client, $this> */
    public function client(): BelongsTo
    {
        return $this->belongsTo(Client::class);
    }

    /** @return HasMany<Invoice, $this> */
    public function invoices(): HasMany
    {
        return $this->hasMany(Invoice::class);
    }
}

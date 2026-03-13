<?php

namespace App\Models;

use Database\Factories\TimekeeperFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Timekeeper extends Model
{
    /** @use HasFactory<TimekeeperFactory> */
    use HasFactory;

    protected $fillable = [
        'name',
        'timekeeper_id_code',
        'classification',
        'hourly_rate',
        'law_firm_id',
    ];

    /** @return array<string, string> */
    protected function casts(): array
    {
        return [
            'hourly_rate' => 'decimal:2',
        ];
    }

    /** @return HasMany<Invoice, $this> */
    public function invoices(): HasMany
    {
        return $this->hasMany(Invoice::class);
    }
}

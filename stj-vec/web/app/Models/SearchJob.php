<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class SearchJob extends Model
{
    use HasUuids;

    protected $fillable = [
        'id',
        'query',
        'driver',
        'status',
        'decomposition',
        'results',
        'total_results',
        'total_searches',
        'duration_ms',
        'error_message',
    ];

    protected function casts(): array
    {
        return [
            'decomposition' => 'array',
            'results' => 'array',
        ];
    }
}

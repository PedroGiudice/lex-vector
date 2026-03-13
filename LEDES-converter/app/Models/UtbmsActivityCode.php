<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class UtbmsActivityCode extends Model
{
    public $timestamps = false;

    public $incrementing = false;

    protected $primaryKey = 'code';

    protected $keyType = 'string';

    protected $fillable = [
        'code',
        'description',
    ];
}

<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class UtbmsTaskCode extends Model
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

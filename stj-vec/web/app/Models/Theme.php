<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Theme extends Model
{
    protected $fillable = ['name', 'toml_config', 'is_active'];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return ['is_active' => 'boolean'];
    }

    public static function active(): ?self
    {
        return static::query()->where('is_active', true)->first();
    }

    public function activate(): void
    {
        static::query()->where('is_active', true)->update(['is_active' => false]);
        $this->update(['is_active' => true]);
    }
}

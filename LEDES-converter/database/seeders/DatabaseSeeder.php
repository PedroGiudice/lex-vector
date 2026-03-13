<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
            UtbmsSeeder::class,
            DefaultDataSeeder::class,
            ExistingMattersSeeder::class,
        ]);
    }
}

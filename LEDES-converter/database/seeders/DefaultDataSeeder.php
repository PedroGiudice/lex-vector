<?php

namespace Database\Seeders;

use App\Models\Client;
use App\Models\Timekeeper;
use Illuminate\Database\Seeder;

class DefaultDataSeeder extends Seeder
{
    public function run(): void
    {
        Client::query()->updateOrCreate(
            ['name' => 'Salesforce, Inc.'],
            [
                'address' => '50 Freemont St. Suite 300, San Francisco CA USA 94105 2231',
                'contact_person' => 'Caitlin May',
            ]
        );

        Timekeeper::query()->updateOrCreate(
            ['timekeeper_id_code' => 'CMR'],
            [
                'name' => 'RODRIGUES, CARLOS MAGNO',
                'classification' => 'PARTNR',
                'hourly_rate' => 300.00,
                'law_firm_id' => 'SF004554',
            ]
        );
    }
}

<?php

namespace Database\Factories;

use App\Models\Timekeeper;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Timekeeper>
 */
class TimekeeperFactory extends Factory
{
    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'name' => strtoupper(fake()->lastName().', '.fake()->firstName()),
            'timekeeper_id_code' => strtoupper(fake()->unique()->lexify('???')),
            'classification' => fake()->randomElement(['PARTNR', 'ASSOC', 'PARALGL', 'OTHR']),
            'hourly_rate' => fake()->randomFloat(2, 150, 500),
            'law_firm_id' => fake()->numerify('SF######'),
        ];
    }
}

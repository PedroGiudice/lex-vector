<?php

namespace Database\Factories;

use App\Models\Client;
use App\Models\Matter;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Matter>
 */
class MatterFactory extends Factory
{
    public function fixedFee(): static
    {
        return $this->state(fn (array $attributes): array => [
            'afa_type' => 'fixed_fee',
        ]);
    }

    public function scheduledFixedFee(): static
    {
        return $this->state(fn (array $attributes): array => [
            'afa_type' => 'scheduled_fixed_fee',
        ]);
    }

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'client_id' => Client::factory(),
            'matter_number' => 'LS-'.fake()->year().'-'.fake()->unique()->numerify('#####'),
            'law_firm_matter_id' => 'LS-'.fake()->year().'-'.fake()->unique()->numerify('#####'),
            'client_matter_id' => fake()->optional()->numerify('CM-####'),
            'description' => fake()->sentence(),
            'afa_type' => 'hourly',
            'open_date' => fake()->optional()->dateTimeBetween('-1 year', 'now'),
        ];
    }
}

<?php

namespace Database\Factories;

use App\Models\Invoice;
use App\Models\Matter;
use App\Models\Timekeeper;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Invoice>
 */
class InvoiceFactory extends Factory
{
    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $billingStart = fake()->dateTimeBetween('-3 months', '-1 month');
        $billingEnd = (clone $billingStart)->modify('last day of this month');

        return [
            'matter_id' => Matter::factory(),
            'timekeeper_id' => Timekeeper::factory(),
            'invoice_number' => (string) fake()->unique()->numberBetween(4000, 9999),
            'invoice_date' => fake()->dateTimeBetween($billingEnd, 'now'),
            'billing_start' => $billingStart,
            'billing_end' => $billingEnd,
            'total' => fake()->randomFloat(2, 500, 10000),
            'description' => fake()->sentence(),
        ];
    }
}

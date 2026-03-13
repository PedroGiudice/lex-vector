<?php

namespace Database\Factories;

use App\Models\Invoice;
use App\Models\InvoiceLineItem;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<InvoiceLineItem>
 */
class InvoiceLineItemFactory extends Factory
{
    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $unitCost = fake()->randomFloat(2, 150, 500);
        $units = fake()->randomFloat(2, 1, 20);
        $total = round($unitCost * $units, 2);

        return [
            'invoice_id' => Invoice::factory(),
            'line_number' => fake()->numberBetween(1, 10),
            'fee_type' => 'F',
            'units' => $units,
            'unit_cost' => $unitCost,
            'adjustment_amount' => 0,
            'total' => $total,
            'line_item_date' => fake()->date(),
            'task_code' => fake()->randomElement(['L100', 'L110', 'L120', 'L210', 'L510']),
            'expense_code' => null,
            'activity_code' => fake()->randomElement(['A101', 'A102', 'A103', 'A104', 'A106']),
            'description' => fake()->sentence(),
        ];
    }
}

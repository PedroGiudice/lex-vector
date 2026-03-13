<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('invoice_line_items', function (Blueprint $table) {
            $table->id();
            $table->foreignId('invoice_id')->constrained()->cascadeOnDelete();
            $table->integer('line_number');
            $table->string('fee_type')->default('F');
            $table->decimal('units', 10, 2);
            $table->decimal('unit_cost', 10, 2);
            $table->decimal('adjustment_amount', 10, 2)->default(0);
            $table->decimal('total', 14, 2);
            $table->date('line_item_date');
            $table->string('task_code');
            $table->string('expense_code')->nullable();
            $table->string('activity_code');
            $table->text('description');
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('invoice_line_items');
    }
};

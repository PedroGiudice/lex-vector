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
        Schema::create('timekeepers', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('timekeeper_id_code')->unique();
            $table->string('classification');
            $table->decimal('hourly_rate', 10, 2);
            $table->string('law_firm_id');
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('timekeepers');
    }
};

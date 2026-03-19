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
        Schema::create('search_jobs', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('query');
            $table->string('driver');  // 'cli' or 'sdk'
            $table->string('status')->default('running'); // running, completed, error, timeout
            $table->json('decomposition')->nullable();
            $table->json('results')->nullable();
            $table->integer('total_results')->nullable();
            $table->integer('total_searches')->nullable();
            $table->integer('duration_ms')->nullable();
            $table->text('error_message')->nullable();
            $table->timestamps();

            $table->index('status');
            $table->index('created_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('search_jobs');
    }
};

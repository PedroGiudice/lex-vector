<?php

namespace App\Providers;

use App\Services\AgentRunner;
use App\Services\AgentRunnerInterface;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->bind(AgentRunnerInterface::class, AgentRunner::class);
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}

<?php

namespace App\Providers;

use App\Services\AgentRunner;
use App\Services\AgentRunnerInterface;
use App\Services\SdkAgentRunner;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->bind(AgentRunnerInterface::class, function () {
            return config('services.agent.driver') === 'sdk'
                ? new SdkAgentRunner
                : new AgentRunner;
        });
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}

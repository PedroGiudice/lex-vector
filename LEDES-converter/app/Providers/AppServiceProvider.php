<?php

namespace App\Providers;

use App\Contracts\LedesGeneratorInterface;
use App\Contracts\LedesValidatorInterface;
use App\Contracts\TextParserInterface;
use App\Services\Ledes1998BGenerator;
use App\Services\LedesValidator;
use App\Services\StatementTextParser;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->bind(TextParserInterface::class, StatementTextParser::class);
        $this->app->bind(LedesGeneratorInterface::class, Ledes1998BGenerator::class);
        $this->app->bind(LedesValidatorInterface::class, LedesValidator::class);
    }

    public function boot(): void
    {
        //
    }
}

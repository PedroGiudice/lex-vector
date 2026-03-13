<?php

namespace App\Console\Commands;

use App\Services\AgentRunnerInterface;
use Illuminate\Console\Command;

class SearchCleanup extends Command
{
    protected $signature = 'search:cleanup {--hours=24 : Max age in hours}';

    protected $description = 'Remove search result files older than the given threshold';

    public function handle(AgentRunnerInterface $runner): int
    {
        $hours = (int) $this->option('hours');
        $removed = $runner->cleanup($hours);

        $this->info("Removed {$removed} files older than {$hours}h.");

        return self::SUCCESS;
    }
}

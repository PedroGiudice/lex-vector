<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;

class GenerateSetupLinks extends Command
{
    protected $signature = 'users:setup-links {--base-url= : Base URL (default: APP_URL)}';

    protected $description = 'Gera links de primeiro acesso para usuarios que ainda nao definiram senha';

    public function handle(): int
    {
        $baseUrl = $this->option('base-url') ?: config('app.url');

        $users = User::query()->where('must_change_password', true)->get();

        if ($users->isEmpty()) {
            $this->info('Todos os usuarios ja definiram senha.');

            return self::SUCCESS;
        }

        $this->info("Links de setup ({$users->count()} usuarios pendentes):");
        $this->newLine();

        foreach ($users as $user) {
            $token = hash('sha256', $user->id.$user->email.$user->created_at);
            $url = "{$baseUrl}/setup?token={$token}";

            $this->line("  <comment>{$user->name}</comment>");
            $this->line("  {$url}");
            $this->newLine();
        }

        $this->warn('Links validos enquanto must_change_password=true. Apos definir senha, o link expira.');

        return self::SUCCESS;
    }
}

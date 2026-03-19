<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class UserSeeder extends Seeder
{
    public function run(): void
    {
        $users = [
            ['name' => 'PGR', 'email' => 'pgr@stj-vec.local'],
            ['name' => 'ABP', 'email' => 'abp@stj-vec.local'],
            ['name' => 'BBT', 'email' => 'bbt@stj-vec.local'],
        ];

        foreach ($users as $userData) {
            User::query()->updateOrCreate(
                ['email' => $userData['email']],
                [
                    'name' => $userData['name'],
                    'password' => Hash::make(Str::random(32)),
                    'must_change_password' => true,
                ]
            );
        }
    }
}

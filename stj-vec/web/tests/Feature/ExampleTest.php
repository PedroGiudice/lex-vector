<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class ExampleTest extends TestCase
{
    use RefreshDatabase;

    public function test_the_application_returns_a_successful_response(): void
    {
        Http::fake(['*/api/filters' => Http::response([])]);

        $this->actingAs(User::factory()->create(['must_change_password' => false]));

        $response = $this->get('/');

        $response->assertStatus(200);
    }
}

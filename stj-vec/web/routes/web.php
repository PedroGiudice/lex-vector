<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\ChannelStreamController;
use App\Http\Controllers\SearchController;
use App\Http\Controllers\SearchStreamController;
use App\Http\Controllers\SetupController;
use Illuminate\Support\Facades\Route;

// Setup (public, token-gated)
Route::get('/setup', [SetupController::class, 'showSetup'])->name('auth.setup.form');
Route::post('/setup', [SetupController::class, 'setup'])->name('auth.setup')->middleware('throttle:5,1');

// Auth (guest)
Route::middleware('guest')->group(function (): void {
    Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
    Route::post('/login', [AuthController::class, 'login'])->middleware('throttle:5,1');
});

// Auth (authenticated)
Route::middleware('auth')->group(function (): void {
    Route::post('/logout', [AuthController::class, 'logout'])->name('logout');
    Route::get('/password/change', [AuthController::class, 'showChangePassword'])->name('auth.password.form');
    Route::post('/password/change', [AuthController::class, 'changePassword'])->name('auth.password.update');
});

// App (authenticated + password changed)
Route::middleware(['auth', 'password.changed'])->group(function (): void {
    Route::get('/', [SearchController::class, 'index'])->name('search.index');
    Route::post('/search', [SearchController::class, 'search'])->name('search.query');
    Route::get('/document/{docId}', [SearchController::class, 'document'])->name('search.document');
    Route::get('/api/document/{docId}', [SearchController::class, 'documentApi'])->name('api.document');
    Route::get('/api/search/{searchId}/stream', [SearchStreamController::class, 'stream'])->name('search.stream');
    Route::get('/api/channel/{requestId}/stream', [ChannelStreamController::class, 'stream'])->name('channel.stream');
    Route::get('/settings/themes', function () {
        return view('settings.themes');
    })->name('settings.themes');
});

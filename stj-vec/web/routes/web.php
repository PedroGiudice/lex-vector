<?php

use App\Http\Controllers\SearchController;
use Illuminate\Support\Facades\Route;

Route::get('/', [SearchController::class, 'index'])->name('search.index');
Route::post('/search', [SearchController::class, 'search'])->name('search.query');
Route::get('/document/{docId}', [SearchController::class, 'document'])->name('search.document');
Route::get('/api/document/{docId}', [SearchController::class, 'documentApi'])->name('api.document');

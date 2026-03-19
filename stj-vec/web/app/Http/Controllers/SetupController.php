<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;

class SetupController extends Controller
{
    public function showSetup(Request $request): \Illuminate\View\View|\Illuminate\Http\RedirectResponse
    {
        $user = $this->resolveUser($request);

        if (! $user) {
            abort(404);
        }

        if (! $user->must_change_password) {
            return redirect()->route('login')->with('status', 'Conta ja configurada. Faca login.');
        }

        return view('auth.setup', ['user' => $user, 'token' => $request->query('token')]);
    }

    public function setup(Request $request): \Illuminate\Http\RedirectResponse
    {
        $user = $this->resolveUser($request);

        if (! $user || ! $user->must_change_password) {
            abort(404);
        }

        $request->validate([
            'password' => ['required', 'confirmed', Password::min(8)],
        ]);

        $user->update([
            'password' => Hash::make($request->input('password')),
            'must_change_password' => false,
        ]);

        Auth::login($user, true);
        $request->session()->regenerate();

        return redirect()->route('search.index');
    }

    private function resolveUser(Request $request): ?User
    {
        $token = $request->query('token');

        if (! $token || ! is_string($token)) {
            return null;
        }

        return User::query()
            ->where('must_change_password', true)
            ->get()
            ->first(fn (User $u) => hash_equals(
                hash('sha256', $u->id.$u->email.$u->created_at),
                $token
            ));
    }
}

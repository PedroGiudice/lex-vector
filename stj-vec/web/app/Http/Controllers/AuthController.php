<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;

class AuthController extends Controller
{
    public function showLogin(): \Illuminate\View\View
    {
        return view('auth.login');
    }

    public function login(Request $request): \Illuminate\Http\RedirectResponse
    {
        $credentials = $request->validate([
            'name' => 'required|string',
            'password' => 'required|string',
        ]);

        if (! Auth::attempt($credentials, $request->boolean('remember'))) {
            return back()
                ->withInput($request->only('name'))
                ->withErrors(['name' => 'Credenciais invalidas.']);
        }

        $request->session()->regenerate();

        if (Auth::user()->must_change_password) {
            return redirect()->route('auth.password.form');
        }

        return redirect()->intended(route('search.index'));
    }

    public function showChangePassword(): \Illuminate\View\View
    {
        return view('auth.change-password');
    }

    public function changePassword(Request $request): \Illuminate\Http\RedirectResponse
    {
        $request->validate([
            'password' => ['required', 'confirmed', Password::min(8)],
        ]);

        /** @var \App\Models\User $user */
        $user = Auth::user();
        $user->update([
            'password' => Hash::make($request->input('password')),
            'must_change_password' => false,
        ]);

        return redirect()->route('search.index')->with('status', 'Senha alterada com sucesso.');
    }

    public function logout(Request $request): \Illuminate\Http\RedirectResponse
    {
        Auth::logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect()->route('login');
    }
}

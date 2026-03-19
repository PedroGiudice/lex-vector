<?php

namespace App\Livewire;

use App\Models\Theme;
use App\Services\Theme\ThemeService;
use App\Services\Theme\TomlParser;
use Livewire\Component;

class ThemeSettings extends Component
{
    public ?int $selectedThemeId = null;

    public string $editorContent = '';

    public string $themeName = '';

    public string $statusMessage = '';

    public string $statusType = 'info';

    public function mount(): void
    {
        $active = Theme::active();

        if ($active) {
            $this->selectTheme($active->id);
        }
    }

    /**
     * @return \Illuminate\Database\Eloquent\Collection<int, Theme>
     */
    public function getThemesProperty(): \Illuminate\Database\Eloquent\Collection
    {
        return Theme::query()->orderBy('name')->get();
    }

    public function selectTheme(int $id): void
    {
        $theme = Theme::query()->findOrFail($id);
        $this->selectedThemeId = $theme->id;
        $this->editorContent = $theme->toml_config;
        $this->themeName = $theme->name;
        $this->clearStatus();
    }

    public function save(): void
    {
        if (! $this->selectedThemeId) {
            return;
        }

        $theme = Theme::query()->findOrFail($this->selectedThemeId);

        $parsed = TomlParser::parse($this->editorContent);

        if ($parsed === []) {
            $this->setStatus('TOML invalido. Verifique a sintaxe.', 'error');

            return;
        }

        $theme->update([
            'name' => $this->themeName,
            'toml_config' => $this->editorContent,
        ]);

        $this->setStatus('Tema salvo.', 'success');
    }

    public function activate(): void
    {
        if (! $this->selectedThemeId) {
            return;
        }

        $theme = Theme::query()->findOrFail($this->selectedThemeId);
        $theme->activate();

        $this->setStatus("Tema \"{$theme->name}\" ativado.", 'success');
    }

    public function deleteTheme(): void
    {
        if (! $this->selectedThemeId) {
            return;
        }

        $theme = Theme::query()->findOrFail($this->selectedThemeId);

        if ($theme->is_active) {
            $this->setStatus('Nao e possivel deletar o tema ativo.', 'error');

            return;
        }

        $theme->delete();
        $this->selectedThemeId = null;
        $this->editorContent = '';
        $this->themeName = '';

        $active = Theme::active();

        if ($active) {
            $this->selectTheme($active->id);
        }

        $this->setStatus('Tema deletado.', 'success');
    }

    public function newTheme(): void
    {
        $count = Theme::query()->count();

        if ($count >= 10) {
            $this->setStatus('Limite de 10 temas atingido.', 'error');

            return;
        }

        $theme = Theme::query()->create([
            'name' => 'Novo Tema '.($count + 1),
            'toml_config' => TomlParser::encode(ThemeService::defaultConfig()),
            'is_active' => false,
        ]);

        $this->selectTheme($theme->id);
        $this->setStatus('Tema criado.', 'success');
    }

    public function resetToDefaults(): void
    {
        $this->editorContent = TomlParser::encode(ThemeService::defaultConfig());
        $this->setStatus('Editor resetado para defaults. Clique Save para aplicar.', 'info');
    }

    public function render(): \Illuminate\View\View
    {
        return view('livewire.theme-settings');
    }

    private function setStatus(string $message, string $type): void
    {
        $this->statusMessage = $message;
        $this->statusType = $type;
    }

    private function clearStatus(): void
    {
        $this->statusMessage = '';
    }
}

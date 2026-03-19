<?php

namespace App\Services\Theme;

use App\Models\Theme;

final class ThemeService
{
    /** @var array<string, string> */
    private const VAR_MAP = [
        'surface.page' => '--c-surface-page',
        'surface.card' => '--c-surface-card',
        'surface.raised' => '--c-surface-raised',
        'surface.sidebar' => '--c-surface-sidebar',
        'surface.header' => '--c-surface-header',
        'surface.overlay' => '--c-surface-overlay',
        'surface.hover' => '--c-surface-hover',
        'text.primary' => '--c-text',
        'text.secondary' => '--c-text-secondary',
        'text.muted' => '--c-text-muted',
        'text.on-header' => '--c-text-on-header',
        'text.on-header-muted' => '--c-text-on-header-muted',
        'text.link' => '--c-text-link',
        'text.link-hover' => '--c-text-link-hover',
        'border.default' => '--c-border',
        'border.subtle' => '--c-border-subtle',
        'border.strong' => '--c-border-strong',
        'border.focus' => '--c-border-focus',
        'accent.primary' => '--c-accent',
        'accent.primary-hover' => '--c-accent-hover',
        'accent.warm' => '--c-accent-warm',
        'accent.warm-bg' => '--c-accent-warm-bg',
        'accent.success' => '--c-accent-success',
        'accent.warning' => '--c-accent-warning',
        'accent.danger' => '--c-accent-danger',
        'input.bg' => '--c-input-bg',
        'input.border' => '--c-input-border',
        'input.focus' => '--c-input-focus',
        'badge.info-bg' => '--c-badge-info-bg',
        'badge.info-text' => '--c-badge-info-text',
        'button.primary-bg' => '--c-btn-primary',
        'button.primary-hover' => '--c-btn-primary-hover',
        'button.primary-text' => '--c-btn-primary-text',
    ];

    /**
     * @return array<string, array<string, string>>
     */
    public static function defaultConfig(): array
    {
        return [
            'surface' => [
                'page' => '#f8f9fb',
                'card' => '#ffffff',
                'raised' => '#f1f3f6',
                'sidebar' => '#ffffff',
                'header' => '#334155',
                'overlay' => 'rgba(0, 0, 0, 0.5)',
                'hover' => 'rgba(51, 65, 85, 0.06)',
            ],
            'text' => [
                'primary' => '#1e293b',
                'secondary' => '#475569',
                'muted' => '#94a3b8',
                'on-header' => '#f1f5f9',
                'on-header-muted' => '#94a3b8',
                'link' => '#2563eb',
                'link-hover' => '#1d4ed8',
            ],
            'border' => [
                'default' => 'rgba(51, 65, 85, 0.15)',
                'subtle' => 'rgba(51, 65, 85, 0.08)',
                'strong' => 'rgba(51, 65, 85, 0.22)',
                'focus' => '#a16a3a',
            ],
            'accent' => [
                'primary' => '#a16a3a',
                'primary-hover' => '#8b5a30',
                'warm' => '#c8956c',
                'warm-bg' => 'rgba(200, 149, 108, 0.12)',
                'success' => '#16a34a',
                'warning' => '#d97706',
                'danger' => '#dc2626',
            ],
            'input' => [
                'bg' => '#ffffff',
                'border' => 'rgba(51, 65, 85, 0.2)',
                'focus' => '#a16a3a',
            ],
            'badge' => [
                'info-bg' => 'rgba(37, 99, 235, 0.1)',
                'info-text' => '#2563eb',
            ],
            'button' => [
                'primary-bg' => '#334155',
                'primary-hover' => '#1e293b',
                'primary-text' => '#ffffff',
            ],
        ];
    }

    public static function cssVariables(): string
    {
        $theme = Theme::active();
        $config = $theme
            ? TomlParser::parse($theme->toml_config)
            : self::defaultConfig();

        $defaults = self::defaultConfig();
        $vars = [];

        foreach (self::VAR_MAP as $path => $cssVar) {
            [$section, $key] = explode('.', $path, 2);
            $value = $config[$section][$key] ?? $defaults[$section][$key] ?? '#000000';
            $vars[] = "  {$cssVar}: {$value};";
        }

        return ":root {\n".implode("\n", $vars)."\n}";
    }
}

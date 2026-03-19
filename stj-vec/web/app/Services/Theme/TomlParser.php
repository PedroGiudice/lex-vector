<?php

namespace App\Services\Theme;

final class TomlParser
{
    /**
     * @return array<string, array<string, string>>
     */
    public static function parse(string $toml): array
    {
        $result = [];
        $currentSection = '';

        foreach (explode("\n", $toml) as $line) {
            $line = trim($line);

            if ($line === '' || str_starts_with($line, '#')) {
                continue;
            }

            if (preg_match('/^\[([a-zA-Z0-9_-]+)\]$/', $line, $m)) {
                $currentSection = $m[1];
                $result[$currentSection] ??= [];

                continue;
            }

            if (preg_match('/^([a-zA-Z0-9_-]+)\s*=\s*"([^"]*)"$/', $line, $m)) {
                if ($currentSection !== '') {
                    $result[$currentSection][$m[1]] = $m[2];
                }
            }
        }

        return $result;
    }

    /**
     * @param  array<string, array<string, string>>  $data
     */
    public static function encode(array $data): string
    {
        $lines = [];

        foreach ($data as $section => $values) {
            $lines[] = "[{$section}]";

            foreach ($values as $key => $value) {
                $lines[] = "{$key} = \"{$value}\"";
            }

            $lines[] = '';
        }

        return implode("\n", $lines);
    }
}

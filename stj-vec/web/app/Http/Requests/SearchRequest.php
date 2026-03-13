<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class SearchRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    /**
     * @return array<string, array<int, string>>
     */
    public function rules(): array
    {
        return [
            'query' => ['required', 'string', 'min:3', 'max:500'],
            'limit' => ['nullable', 'integer', 'min:1', 'max:100'],
            'filters.ministro' => ['nullable', 'string'],
            'filters.tipo' => ['nullable', 'string'],
            'filters.classe' => ['nullable', 'string'],
            'filters.orgao_julgador' => ['nullable', 'string'],
            'filters.data_from' => ['nullable', 'date_format:Y-m-d'],
            'filters.data_to' => ['nullable', 'date_format:Y-m-d'],
        ];
    }

    /**
     * @return array<string, string>
     */
    public function messages(): array
    {
        return [
            'query.required' => 'A consulta e obrigatoria.',
            'query.min' => 'A consulta deve ter pelo menos 3 caracteres.',
            'query.max' => 'A consulta deve ter no maximo 500 caracteres.',
        ];
    }

    /**
     * Build the search payload for the Rust backend.
     *
     * @return array<string, mixed>
     */
    public function toPayload(): array
    {
        $payload = ['query' => $this->validated('query')];

        if ($this->filled('limit')) {
            $payload['limit'] = (int) $this->validated('limit');
        }

        $filters = array_filter($this->validated('filters') ?? []);
        if ($filters !== []) {
            $payload['filters'] = $filters;
        }

        return $payload;
    }
}

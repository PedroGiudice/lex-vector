<?php

namespace App\Contracts;

interface LedesGeneratorInterface
{
    /**
     * Gera o conteudo de um arquivo LEDES 1998B.
     *
     * @param  array<string, mixed>  $data  Dados estruturados da invoice
     */
    public function generate(array $data): string;
}

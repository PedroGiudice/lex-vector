<?php

namespace App\Enums;

enum EntryType: string
{
    case User = 'user';
    case Assistant = 'assistant';
    case System = 'system';
    case Summary = 'summary';
}

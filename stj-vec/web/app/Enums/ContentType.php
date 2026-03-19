<?php

namespace App\Enums;

enum ContentType: string
{
    case Text = 'text';
    case Thinking = 'thinking';
    case ToolUse = 'tool_use';
    case ToolResult = 'tool_result';
    case Image = 'image';
}

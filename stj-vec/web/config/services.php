<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    |
    | This file is for storing the credentials for third party services such
    | as Mailgun, Postmark, AWS and more. This file provides the de facto
    | location for this type of information, allowing packages to have
    | a conventional file to locate the various service credentials.
    |
    */

    'postmark' => [
        'key' => env('POSTMARK_API_KEY'),
    ],

    'resend' => [
        'key' => env('RESEND_API_KEY'),
    ],

    'ses' => [
        'key' => env('AWS_ACCESS_KEY_ID'),
        'secret' => env('AWS_SECRET_ACCESS_KEY'),
        'region' => env('AWS_DEFAULT_REGION', 'us-east-1'),
    ],

    'slack' => [
        'notifications' => [
            'bot_user_oauth_token' => env('SLACK_BOT_USER_OAUTH_TOKEN'),
            'channel' => env('SLACK_BOT_USER_DEFAULT_CHANNEL'),
        ],
    ],

    'stj_search' => [
        'url' => env('STJ_SEARCH_URL', 'http://localhost:8421'),
    ],

    'agent' => [
        'path' => env('AGENT_PATH', '/home/opc/.claude/agents/query-decomposer.md'),
        'claude_bin' => env('CLAUDE_BIN', '/home/opc/.local/bin/claude'),
        'model' => env('AGENT_MODEL', 'sonnet'),
        'timeout' => (int) env('AGENT_TIMEOUT', 600),
    ],

];

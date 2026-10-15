<?php

declare(strict_types=1);

$databasePort = filter_var($_ENV['DB_PORT'] ?? '3306', FILTER_VALIDATE_INT);

if ($databasePort === false || $databasePort < 1 || $databasePort > 65535) {
    throw new InvalidArgumentException('DB_PORT must be an integer between 1 and 65535.');
}

return [
    'name' => $_ENV['APP_NAME'] ?? 'EduKit',
    'environment' => $_ENV['APP_ENV'] ?? 'production',
    'debug' => filter_var($_ENV['APP_DEBUG'] ?? 'false', FILTER_VALIDATE_BOOL),
    'timezone' => $_ENV['APP_TIMEZONE'] ?? 'UTC',
    'database' => [
        'host' => $_ENV['DB_HOST'] ?? '127.0.0.1',
        'port' => $databasePort,
        'database' => $_ENV['DB_DATABASE'] ?? 'edukit',
        'username' => $_ENV['DB_USERNAME'] ?? 'edukit_app',
        'password' => $_ENV['DB_PASSWORD'] ?? '',
    ],
    'log_path' => dirname(__DIR__) . DIRECTORY_SEPARATOR . 'storage' . DIRECTORY_SEPARATOR . 'logs' . DIRECTORY_SEPARATOR . 'app.log',
    'views_path' => dirname(__DIR__) . DIRECTORY_SEPARATOR . 'resources' . DIRECTORY_SEPARATOR . 'views',
];

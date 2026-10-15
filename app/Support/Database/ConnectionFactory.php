<?php

declare(strict_types=1);

namespace EduKit\Support\Database;

use InvalidArgumentException;
use PDO;

final class ConnectionFactory
{
    public function __construct(
        private readonly string $host,
        private readonly int $port,
        private readonly string $database,
        private readonly string $username,
        private readonly string $password,
    ) {
        if (!preg_match('/\A[a-zA-Z0-9._:-]+\z/', $host)) {
            throw new InvalidArgumentException('The database host contains unsupported characters.');
        }

        if ($port < 1 || $port > 65535) {
            throw new InvalidArgumentException('The database port must be between 1 and 65535.');
        }

        if (!preg_match('/\A[a-zA-Z0-9_]+\z/', $database)) {
            throw new InvalidArgumentException('The database name contains unsupported characters.');
        }
    }

    public function create(): PDO
    {
        $dsn = sprintf(
            'mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
            $this->host,
            $this->port,
            $this->database,
        );

        return new PDO($dsn, $this->username, $this->password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
    }
}

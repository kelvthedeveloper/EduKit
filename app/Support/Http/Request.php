<?php

declare(strict_types=1);

namespace EduKit\Support\Http;

final class Request
{
    public readonly string $method;
    public readonly string $path;
    private readonly bool $valid;

    public function __construct(
        string $method,
        string $path,
    ) {
        $this->valid = preg_match('/\A[!#$%&\'*+.^_`|~0-9A-Z-]+\z/i', $method) === 1
            && str_starts_with($path, '/')
            && preg_match('/[\x00-\x1F\x7F]/', $path) !== 1;
        $this->method = $this->valid ? strtoupper($method) : '';
        $this->path = $path;
    }

    public function isValid(): bool
    {
        return $this->valid;
    }

    public static function fromGlobals(): self
    {
        $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
        $uri = $_SERVER['REQUEST_URI'] ?? '/';
        if (!is_string($method) || !is_string($uri)) {
            return new self('', '');
        }

        $path = parse_url($uri, PHP_URL_PATH);

        return new self($method, is_string($path) ? $path : '');
    }
}

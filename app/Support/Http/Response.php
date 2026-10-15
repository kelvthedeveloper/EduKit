<?php

declare(strict_types=1);

namespace EduKit\Support\Http;

final class Response
{
    /**
     * @param array<string, string> $headers
     */
    public function __construct(
        private readonly string $body,
        private readonly int $statusCode = 200,
        private readonly array $headers = ['Content-Type' => 'text/html; charset=UTF-8'],
    ) {
    }

    /**
     * @param array<string, string> $headers
     */
    public static function html(string $body, int $statusCode = 200, array $headers = []): self
    {
        return new self($body, $statusCode, ['Content-Type' => 'text/html; charset=UTF-8'] + $headers);
    }

    /**
     * @param array<string, string> $headers
     */
    public static function json(array $data, int $statusCode = 200): self
    {
        $body = json_encode($data, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES);

        return new self($body, $statusCode, ['Content-Type' => 'application/json; charset=UTF-8']);
    }

    public function body(): string
    {
        return $this->body;
    }

    public function statusCode(): int
    {
        return $this->statusCode;
    }

    /**
     * @return array<string, string>
     */
    public function headers(): array
    {
        return $this->headers;
    }

    public function send(): void
    {
        http_response_code($this->statusCode);

        foreach ($this->headers as $name => $value) {
            header($name . ': ' . $value);
        }

        echo $this->body;
    }
}

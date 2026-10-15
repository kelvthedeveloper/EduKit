<?php

declare(strict_types=1);

namespace EduKit\Support;

use InvalidArgumentException;
use RuntimeException;
use Throwable;

final class View
{
    public function __construct(private readonly string $directory)
    {
    }

    /**
     * @param array<string, mixed> $data
     */
    public function render(string $template, array $data = []): string
    {
        if (!preg_match('/\A[a-zA-Z0-9_-]+\z/', $template)) {
            throw new InvalidArgumentException('View names may contain only letters, numbers, underscores, and hyphens.');
        }

        $path = $this->directory . DIRECTORY_SEPARATOR . $template . '.php';

        if (!is_file($path)) {
            throw new RuntimeException(sprintf('View "%s" was not found.', $template));
        }

        extract($data, EXTR_SKIP);
        ob_start();

        try {
            require $path;

            return (string) ob_get_clean();
        } catch (Throwable $exception) {
            ob_end_clean();

            throw $exception;
        }
    }
}

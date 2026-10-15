<?php

declare(strict_types=1);

namespace EduKit\Support\Http;

use Psr\Log\LoggerInterface;
use Throwable;

final class Kernel
{
    public function __construct(
        private readonly Router $router,
        private readonly LoggerInterface $logger,
    ) {
    }

    public function handle(Request $request): Response
    {
        try {
            return $this->router->dispatch($request);
        } catch (Throwable $exception) {
            try {
                $this->logger->error('Unhandled application exception.', [
                    'exception' => $exception,
                    'method' => $request->method,
                    'path' => $request->path,
                ]);
            } catch (Throwable) {
                error_log('EduKit could not write an unhandled exception to the application log.');
            }

            return Response::html('<h1>Internal Server Error</h1>', 500);
        }
    }
}

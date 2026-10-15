<?php

declare(strict_types=1);

namespace EduKit\Support\Http;

use LogicException;

final class Router
{
    /** @var array<string, array<string, string>> */
    private array $routes = [];

    /** @var array<string, callable(Request): Response> */
    private array $handlers = [];

    /**
     * @param callable(Request): Response $handler
     */
    public function registerHandler(string $name, callable $handler): void
    {
        if (!preg_match('/\A[a-zA-Z][a-zA-Z0-9_.-]*\z/', $name)) {
            throw new LogicException('Handler names must start with a letter and contain only letters, numbers, dots, underscores, or hyphens.');
        }

        if (isset($this->handlers[$name])) {
            throw new LogicException(sprintf('A handler named "%s" is already registered.', $name));
        }

        $this->handlers[$name] = $handler;
    }

    public function get(string $path, string $handlerName): void
    {
        $this->add('GET', $path, $handlerName);
    }

    public function post(string $path, string $handlerName): void
    {
        $this->add('POST', $path, $handlerName);
    }

    public function dispatch(Request $request): Response
    {
        if (!$request->isValid()) {
            return Response::html('<h1>Bad Request</h1>', 400);
        }

        $route = $this->routes[$request->path] ?? null;

        if ($route === null) {
            return Response::html('<h1>Not Found</h1>', 404);
        }

        $handlerName = $route[$request->method] ?? null;

        if ($handlerName === null) {
            return Response::html('<h1>Method Not Allowed</h1>', 405, [
                'Allow' => implode(', ', array_keys($route)),
            ]);
        }

        $handler = $this->handlers[$handlerName] ?? null;

        if ($handler === null) {
            throw new LogicException(sprintf('The handler "%s" was not registered.', $handlerName));
        }

        $response = $handler($request);

        if (!$response instanceof Response) {
            throw new LogicException('A route handler must return an HTTP response.');
        }

        return $response;
    }

    private function add(string $method, string $path, string $handlerName): void
    {
        if (!preg_match('/\A\/(?:[a-zA-Z0-9_.-]+(?:\/[a-zA-Z0-9_.-]+)*)?\z/', $path)) {
            throw new LogicException('Route paths must be absolute, normalized paths.');
        }

        $segments = explode('/', trim($path, '/'));
        if (array_intersect($segments, ['.', '..']) !== []) {
            throw new LogicException('Route paths cannot contain dot segments.');
        }

        if (isset($this->routes[$path][$method])) {
            throw new LogicException(sprintf('A %s route for "%s" is already registered.', $method, $path));
        }

        $this->routes[$path][$method] = $handlerName;
    }
}

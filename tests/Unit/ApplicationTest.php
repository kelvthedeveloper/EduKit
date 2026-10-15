<?php

declare(strict_types=1);

namespace EduKit\Tests\Unit;

use EduKit\Support\Container;
use EduKit\Support\Http\Request;
use EduKit\Support\Http\Response;
use EduKit\Support\Http\Router;
use EduKit\Support\View;
use EduKit\Controllers\HomeController;
use PHPUnit\Framework\TestCase;

final class ApplicationTest extends TestCase
{
    public function test_health_route_returns_only_a_minimal_status(): void
    {
        $router = new Router();
        $registerRoutes = require dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'routes' . DIRECTORY_SEPARATOR . 'web.php';
        $registerRoutes($router, new Container());

        $response = $router->dispatch(new Request('GET', '/health'));

        self::assertSame(200, $response->statusCode());
        self::assertSame(['Content-Type' => 'application/json; charset=UTF-8'], $response->headers());
        self::assertSame('{"status":"ok"}', $response->body());
    }

    public function test_health_route_does_not_accept_post(): void
    {
        $router = new Router();
        $registerRoutes = require dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'routes' . DIRECTORY_SEPARATOR . 'web.php';
        $registerRoutes($router, new Container());

        $response = $router->dispatch(new Request('POST', '/health'));

        self::assertSame(405, $response->statusCode());
        self::assertSame('GET', $response->headers()['Allow']);
    }

    public function test_home_page_uses_a_layout_and_escapes_the_application_name(): void
    {
        $view = new View(dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'resources' . DIRECTORY_SEPARATOR . 'views');
        $controller = new HomeController($view, '<EduKit>');
        $response = $controller(new Request('GET', '/'));

        self::assertSame(200, $response->statusCode());
        self::assertStringContainsString('<!doctype html>', $response->body());
        self::assertStringContainsString('&lt;EduKit&gt;', $response->body());
        self::assertStringNotContainsString('<title><EduKit></title>', $response->body());
    }
}

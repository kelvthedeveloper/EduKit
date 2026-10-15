<?php

declare(strict_types=1);

namespace EduKit\Tests\Unit;

use EduKit\Support\Http\Request;
use EduKit\Support\Http\Response;
use EduKit\Support\Http\Router;
use LogicException;
use PHPUnit\Framework\TestCase;

final class RouterTest extends TestCase
{
    public function test_dispatches_a_matching_get_route(): void
    {
        $router = new Router();
        $router->registerHandler('ready', static fn (Request $request): Response => Response::html('ready'));
        $router->get('/ready', 'ready');

        $response = $router->dispatch(new Request('GET', '/ready'));

        self::assertSame(200, $response->statusCode());
        self::assertSame('ready', $response->body());
    }

    public function test_returns_not_found_for_an_unmatched_route(): void
    {
        $response = (new Router())->dispatch(new Request('GET', '/missing'));

        self::assertSame(404, $response->statusCode());
        self::assertSame('<h1>Not Found</h1>', $response->body());
    }

    public function test_dispatches_a_named_post_handler(): void
    {
        $router = new Router();
        $router->registerHandler('submit.form', static fn (Request $request): Response => Response::html('submitted'));
        $router->post('/form', 'submit.form');

        $response = $router->dispatch(new Request('POST', '/form'));

        self::assertSame(200, $response->statusCode());
        self::assertSame('submitted', $response->body());
    }

    public function test_returns_method_not_allowed_for_a_known_path(): void
    {
        $router = new Router();
        $router->registerHandler('read', static fn (Request $request): Response => Response::html('read'));
        $router->get('/record', 'read');

        $response = $router->dispatch(new Request('PUT', '/record'));

        self::assertSame(405, $response->statusCode());
        self::assertSame('GET', $response->headers()['Allow']);
    }

    public function test_returns_bad_request_for_an_invalid_method_or_path(): void
    {
        $router = new Router();

        self::assertSame(400, $router->dispatch(new Request('GET', 'health'))->statusCode());
        self::assertSame(400, $router->dispatch(new Request('BAD METHOD', '/'))->statusCode());
    }

    public function test_rejects_dot_segments_in_route_paths(): void
    {
        $router = new Router();
        $router->registerHandler('record', static fn (Request $request): Response => Response::html('record'));

        $this->expectException(LogicException::class);
        $router->get('/records/..', 'record');
    }
}

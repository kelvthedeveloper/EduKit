<?php

declare(strict_types=1);

namespace EduKit\Tests\Unit;

use EduKit\Support\Http\Kernel;
use EduKit\Support\Http\Request;
use EduKit\Support\Http\Response;
use EduKit\Support\Http\Router;
use Monolog\Handler\TestHandler;
use Monolog\Logger;
use PHPUnit\Framework\TestCase;
use RuntimeException;

final class KernelTest extends TestCase
{
    public function test_logs_unhandled_errors_and_returns_a_generic_response(): void
    {
        $router = new Router();
        $router->registerHandler('broken', static function (Request $request): Response {
            throw new RuntimeException('Sensitive database details.');
        });
        $router->get('/broken', 'broken');

        $handler = new TestHandler();
        $logger = new Logger('test');
        $logger->pushHandler($handler);
        $response = (new Kernel($router, $logger))->handle(new Request('GET', '/broken'));

        self::assertSame(500, $response->statusCode());
        self::assertStringNotContainsString('Sensitive database details.', $response->body());
        self::assertTrue($handler->hasErrorRecords());
    }
}

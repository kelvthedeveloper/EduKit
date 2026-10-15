<?php

declare(strict_types=1);

namespace EduKit\Tests\Unit;

use EduKit\Support\Container;
use PHPUnit\Framework\TestCase;
use RuntimeException;
use stdClass;

final class ContainerTest extends TestCase
{
    public function test_resolves_and_caches_a_service(): void
    {
        $container = new Container();
        $container->set(stdClass::class, static fn (): stdClass => new stdClass());

        self::assertSame($container->get(stdClass::class), $container->get(stdClass::class));
    }

    public function test_throws_when_a_service_is_not_registered(): void
    {
        $this->expectException(RuntimeException::class);

        (new Container())->get(stdClass::class);
    }
}

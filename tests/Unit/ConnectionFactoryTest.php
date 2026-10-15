<?php

declare(strict_types=1);

namespace EduKit\Tests\Unit;

use EduKit\Support\Database\ConnectionFactory;
use InvalidArgumentException;
use PHPUnit\Framework\TestCase;

final class ConnectionFactoryTest extends TestCase
{
    public function test_rejects_a_database_name_that_could_modify_the_dsn(): void
    {
        $this->expectException(InvalidArgumentException::class);

        new ConnectionFactory('localhost', 3306, 'school;host=untrusted', 'user', 'password');
    }

    public function test_rejects_an_invalid_port(): void
    {
        $this->expectException(InvalidArgumentException::class);

        new ConnectionFactory('localhost', 70000, 'edukit', 'user', 'password');
    }
}

<?php

declare(strict_types=1);

namespace EduKit\Tests\Unit;

use EduKit\Support\View;
use InvalidArgumentException;
use PHPUnit\Framework\TestCase;

final class ViewTest extends TestCase
{
    public function test_escapes_dynamic_template_values(): void
    {
        $view = new View(dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'resources' . DIRECTORY_SEPARATOR . 'views');

        $html = $view->render('layout', [
            'appName' => '<script>alert(1)</script>',
            'content' => '',
        ]);

        self::assertStringNotContainsString('<script>', $html);
        self::assertStringContainsString('&lt;script&gt;', $html);
    }

    public function test_rejects_template_path_traversal(): void
    {
        $view = new View(dirname(__DIR__, 2) . DIRECTORY_SEPARATOR . 'resources' . DIRECTORY_SEPARATOR . 'views');

        $this->expectException(InvalidArgumentException::class);
        $view->render('../outside');
    }
}

<?php

declare(strict_types=1);

use EduKit\Controllers\HomeController;
use EduKit\Support\Container;
use EduKit\Support\Http\Request;
use EduKit\Support\Http\Response;
use EduKit\Support\Http\Router;

return static function (Router $router, Container $container): void {
    $router->registerHandler('home', static function (Request $request) use ($container): Response {
        $controller = $container->get(HomeController::class);

        return $controller($request);
    });
    $router->registerHandler('health', static fn (Request $request): Response => Response::json(['status' => 'ok']));
    $router->get('/', 'home');
    $router->get('/health', 'health');
};

<?php

declare(strict_types=1);

use EduKit\Controllers\HomeController;
use EduKit\Support\Container;
use EduKit\Support\Database\ConnectionFactory;
use EduKit\Support\Http\Kernel;
use EduKit\Support\Http\Router;
use EduKit\Support\View;
use Monolog\Formatter\JsonFormatter;
use Monolog\Handler\StreamHandler;
use Monolog\Level;
use Monolog\Logger;

require dirname(__DIR__) . DIRECTORY_SEPARATOR . 'vendor' . DIRECTORY_SEPARATOR . 'autoload.php';

Dotenv\Dotenv::createImmutable(dirname(__DIR__))->safeLoad();
$config = require dirname(__DIR__) . DIRECTORY_SEPARATOR . 'config' . DIRECTORY_SEPARATOR . 'app.php';
date_default_timezone_set($config['timezone']);

$handler = new StreamHandler($config['log_path'], $config['debug'] ? Level::Debug : Level::Info);
$handler->setFormatter(new JsonFormatter());
$logger = new Logger('edukit');
$logger->pushHandler($handler);

$container = new Container();
$container->set(View::class, static function () use ($config): View {
    return new View($config['views_path']);
});
$container->set(ConnectionFactory::class, static function () use ($config): ConnectionFactory {
    return new ConnectionFactory(
        $config['database']['host'],
        $config['database']['port'],
        $config['database']['database'],
        $config['database']['username'],
        $config['database']['password'],
    );
});
$container->set(HomeController::class, static function (Container $container) use ($config): HomeController {
    return new HomeController($container->get(View::class), $config['name']);
});

$router = new Router();
$registerRoutes = require dirname(__DIR__) . DIRECTORY_SEPARATOR . 'routes' . DIRECTORY_SEPARATOR . 'web.php';
$registerRoutes($router, $container);

return new Kernel($router, $logger);

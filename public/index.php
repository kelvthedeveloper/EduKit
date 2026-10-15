<?php

declare(strict_types=1);

use EduKit\Support\Http\Request;

ini_set('display_errors', '0');
ini_set('log_errors', '1');

try {
    $kernel = require dirname(__DIR__) . DIRECTORY_SEPARATOR . 'bootstrap' . DIRECTORY_SEPARATOR . 'app.php';
    $kernel->handle(Request::fromGlobals())->send();
} catch (\Throwable $exception) {
    error_log('EduKit failed to initialize the request: ' . $exception);
    http_response_code(500);
    header('Content-Type: text/html; charset=UTF-8');
    echo '<h1>Internal Server Error</h1>';
}

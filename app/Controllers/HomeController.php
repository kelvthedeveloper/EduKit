<?php

declare(strict_types=1);

namespace EduKit\Controllers;

use EduKit\Support\Http\Request;
use EduKit\Support\Http\Response;
use EduKit\Support\View;

final class HomeController
{
    public function __construct(
        private readonly View $view,
        private readonly string $appName,
    ) {
    }

    public function __invoke(Request $request): Response
    {
        $content = $this->view->render('home', [
            'appName' => $this->appName,
        ]);

        return Response::html($this->view->render('layout', [
            'appName' => $this->appName,
            'content' => $content,
        ]));
    }
}

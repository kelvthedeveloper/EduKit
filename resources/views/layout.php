<?php

declare(strict_types=1);

$safeAppName = htmlspecialchars((string) $appName, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= $safeAppName ?></title>
    <link rel="stylesheet" href="/assets/app.css">
</head>
<body class="min-h-screen bg-slate-100 text-slate-900">
    <main class="mx-auto flex min-h-screen max-w-5xl items-center justify-center px-6">
        <?= $content ?>
    </main>
</body>
</html>

<?php

declare(strict_types=1);

$safeAppName = htmlspecialchars((string) $appName, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
?>
<section class="rounded-xl bg-white p-8 text-center shadow-sm">
    <h1 class="text-3xl font-semibold"><?= $safeAppName ?></h1>
    <p class="mt-3 text-slate-600">The application foundation is ready.</p>
</section>

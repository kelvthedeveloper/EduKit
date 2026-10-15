# EduKit architecture

EduKit uses a custom MVC architecture rather than a full-stack framework. The PHP application targets PHP 8.3 or later and is served by Apache with `public/` as its document root.

## Request flow

`public/index.php` loads the bootstrap, builds the dependency container and routes, then passes a request to the HTTP kernel. The router dispatches to a controller, controllers return HTTP responses, and views render escaped server-side templates. The kernel logs unhandled exceptions and always returns a generic 500 response; debug settings never expose exception details to users.

## Boundaries

- Controllers coordinate HTTP input and output; business rules belong in services.
- Repositories own database queries; use PDO prepared statements through `ConnectionFactory` (`PDO::ATTR_EMULATE_PREPARES` is disabled).
- Models represent domain concepts where useful.
- Middleware will own authentication, authorization, and CSRF enforcement as those features are added.
- Configuration is read from environment variables. Secrets must not be committed.
- Logs, uploads, and backups belong under `storage/`, outside the web document root.
- Versioned SQL migrations belong under `database/migrations/`. No schema or migration runner is included in this bootstrap.
- Tailwind is compiled into `public/assets/app.css`; the deployed application does not load assets from a CDN.

## Initial implementation choices

- Composer provides PSR-4 autoloading and locks PHP dependencies in `composer.lock`.
- A small explicit container keeps wiring visible without reflection-based autowiring.
- The router supports named GET and POST handlers, returns 404 for unknown paths, and 405 with an `Allow` header for unsupported methods on known paths.
- Monolog writes JSON-formatted application events to `storage/logs/app.log`.
- The frontend uses pinned npm dependencies and `package-lock.json`.
- `GET /health` returns a minimal JSON availability status and intentionally does not reveal database connectivity or diagnostics.

## Local setup

1. Install PHP 8.3+, Composer, Node.js/npm, and Apache with `mod_rewrite`.
2. Run `composer install` and `npm ci`.
3. Copy `.env.example` to `.env`; keep debug disabled outside local development.
4. Run `npm run build`.
5. Configure the Apache virtual host's document root as the absolute path to this repository's `public/` directory. Allow `.htaccess` overrides or move the rewrite rules into the virtual-host configuration.
6. Run `composer test`.

The MariaDB connection factory is lazy and reads its connection settings from environment-backed configuration. Database schema, migrations, authentication, and business modules are intentionally deferred.

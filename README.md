# EduKit

EduKit is a custom PHP school-management application for local-network deployment. This phase provides the project foundation only; authentication and school business modules have not been implemented.

## Requirements

- PHP 8.3 or later with `pdo_mysql`, `mbstring`, and `openssl` enabled
- Composer 2
- Node.js and npm
- Apache with `mod_rewrite` enabled
- MariaDB 10.6 or later for the configured PDO connection

## Development on Windows with XAMPP

Use XAMPP for local development on Windows. In the XAMPP Control Panel, start Apache and MariaDB. Ensure the PHP CLI used by Composer is PHP 8.3 or later and has `pdo_mysql`, `mbstring`, and `openssl` enabled. Install Composer and Node.js/npm separately if they are not already available.

1. From the repository root, install dependencies:

   ```powershell
   composer install
   npm ci
   ```

2. Copy `.env.example` to `.env`. Set a local MariaDB username and password; never commit `.env`.
3. Create the local database and a restricted application user in MariaDB. For example, replace the password and bind the account to localhost:

   ```sql
   CREATE DATABASE edukit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'edukit_app'@'localhost' IDENTIFIED BY 'replace-with-a-unique-password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON edukit.* TO 'edukit_app'@'localhost';
   FLUSH PRIVILEGES;
   ```

   The application does not yet contain a schema or migration runner. Do not grant schema-administration permissions to the runtime account.
4. Compile the local Tailwind stylesheet:

   ```powershell
   npm run build
   ```

5. Run the test suite:

   ```powershell
   composer test
   ```

6. To preview with PHP's development server (not for production):

   ```powershell
   php -S 127.0.0.1:8000 -t public
   ```

   Visit `http://127.0.0.1:8000/`; `http://127.0.0.1:8000/health` returns only `{"status":"ok"}` and does not test or disclose database diagnostics.

The application can also be served locally by the XAMPP Apache instance. Configure its virtual host's document root to the repository's `public/` directory; do not use the repository root as the web root.

## School server deployment on Ubuntu

The production school server is expected to run Ubuntu. Keep the Windows/XAMPP development environment separate from the Ubuntu deployment: configure PHP, Apache, MariaDB, paths, permissions, and environment variables on the Ubuntu host rather than copying Windows/XAMPP settings.

1. Install Apache, MariaDB, PHP 8.3 or later, and the PHP extensions required by the application. On an Ubuntu release whose configured repositories provide the required PHP version, the package names are typically:

   ```bash
   sudo apt update
   sudo apt install apache2 mariadb-server php php-cli libapache2-mod-php php-mysql php-mbstring php-xml composer
   sudo a2enmod rewrite
   ```

   Check the Ubuntu release's PHP packages first; use a supported PHP 8.3+ package source if the default repositories are older. Verify the PHP version and `pdo_mysql` extension for both CLI and Apache.
2. Deploy the project to a protected application directory such as `/var/www/edukit`. Configure the Apache virtual host's `DocumentRoot` as `/var/www/edukit/public` only. Do not expose the repository root, `.env`, `vendor/`, `storage/`, or source/configuration folders. Permit `.htaccess` overrides for `public/.htaccess`, or copy its rewrite rules into the virtual-host configuration.
3. Install production PHP dependencies from the application directory with `composer install --no-dev --classmap-authoritative`. Build the Tailwind asset before deployment (`npm ci` and `npm run build` on a development/build machine), then deploy the generated `public/assets/app.css`; Node.js is not needed to serve the application.
4. Create the MariaDB database and a dedicated runtime account with only the required data permissions. Configure production values in the service environment or a protected `.env` file that is not served by Apache. Set `APP_ENV=production`, `APP_DEBUG=false`, and unique database credentials; do not reuse the local XAMPP password.
5. Grant the Apache service account write access only to required runtime directories such as `storage/logs`, `storage/uploads`, and `storage/backups`; keep application source and configuration read-only to that account where practical. Restrict `.env` permissions to the deployment/application administrators.
6. Keep MariaDB bound to localhost unless a separately protected database host is required. Restrict network access with the Ubuntu firewall so only intended school LAN clients can reach the web service; do not expose MariaDB to the public internet.
7. Use HTTPS for browser traffic, keep production error details in protected logs, and rotate/secure logs and backups. The `/health` route reports application availability only; it intentionally does not reveal whether MariaDB is reachable.

## Project layout

- `app/` — controllers and support services, including HTTP routing and PDO connection factory
- `bootstrap/`, `config/`, `routes/` — application wiring, configuration, and route definitions
- `database/migrations/`, `database/seeders/` — reserved for future versioned database work
- `public/` — the only web document root; front controller and compiled assets
- `resources/` — server-rendered PHP templates and Tailwind source CSS
- `storage/` — protected runtime logs, uploads, and backups
- `tests/` — PHPUnit tests

Student, finance, examination, attendance, authentication, and complete database-schema features are not part of this foundation phase.

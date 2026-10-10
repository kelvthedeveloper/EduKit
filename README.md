# EduKit

EduKit is a local-first digital transformation system for schools. Each school
will run an independent installation with its own database. EduKit is not a
multi-tenant SaaS product.

The initial repository contains a Next.js web application and a Django REST
Framework API. No school-specific modules have been implemented yet.

## Repository structure

- `apps/web/` — Next.js App Router frontend using React and TypeScript.
- `apps/api/` — Django project and Django REST Framework API.
- `packages/ui/` — reserved for future shared UI components.
- `packages/config/` — reserved for future shared configuration.
- `infrastructure/docker/` — reserved for deployment assets, as needed.
- `infrastructure/nginx/` — reserved for reverse-proxy configuration, as needed.
- `infrastructure/deployment/` — reserved for deployment documentation and assets.
- `docs/` — architecture and project documentation.
- `scripts/` — reserved for developer and maintenance scripts.

See [docs/architecture.md](docs/architecture.md) for the local-first deployment
model and [AGENTS.md](AGENTS.md) for repository architecture rules.

## Prerequisites

- Node.js 20.9 or newer and npm.
- Python 3.12 or newer (use a release supported by Django 6.1).

The initial setup was verified with Node.js 24.21.0, npm 11.19.0, and Python
3.15.0.

## Initial development setup

From the repository root, install frontend dependencies and start Next.js:

```powershell
npm install
npm run dev
```

Open <http://localhost:3000>.

Create and activate a Python virtual environment, install the API dependencies,
and start Django:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps\api\requirements.txt
python apps\api\manage.py runserver
```

The API development server is available at <http://127.0.0.1:8000>. Django uses
SQLite by default for local development; no database setup is required.

The root `.env.example` documents placeholder environment variables. Django
reads them from the process environment; no dotenv loader is included. It
contains no usable credentials. Do not commit real secrets.

## Checks

Run frontend lint and TypeScript checks from the repository root:

```powershell
npm run lint
npm run typecheck
```

Run Django's system checks from the repository root with the virtual environment
activated:

```powershell
python apps\api\manage.py check
```

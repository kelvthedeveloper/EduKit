# EduKit architecture

## Product and deployment model

EduKit is independently installed by each school. It is not a SaaS product and
does not use a shared multi-tenant database. Every school installation owns and
controls its own application instance and database.

The local school installation is the operational system of record and must
continue working when internet access is unavailable. Its application and
database are for local use and must not be exposed directly to the public
internet.

A separate cloud deployment may provide remote access, synchronization, online
admissions, notifications, and other cloud capabilities. It is a distinct
deployment from a school's local installation, not a second copy of the
frontend/backend codebase and not a shared tenant host. Cloud connectivity must
not be required for core local operation.

## Application boundaries

- `apps/web/` contains the Next.js user interface.
- `apps/api/` contains Django and Django REST Framework. Django owns business
  logic, authorization, and all database access.
- The web application communicates with the API over HTTP; it must never
  connect directly to PostgreSQL.
- Each installation uses its own database. The starter API uses SQLite for
  zero-configuration local development; production database choices and
  deployment configuration are intentionally not introduced by this
  initialization.

## Offline operation and future synchronization

Core local workflows must remain available without internet connectivity. Any
future synchronization with cloud services must tolerate retries and duplicate
delivery and use idempotent processing. Local data remains usable while
disconnected; network availability must not become a prerequisite for local
school operations.

NFC card identifiers are not permanent student identities. Future attendance
records must be event-based. These constraints are recorded now so subsequent
feature work follows the domain boundaries without implementing those features
in this initialization.

## Repository scope

This repository currently initializes the frontend, API, and documentation
structure only. It does not implement student, attendance, NFC, finance,
admissions, or other school modules, nor does it add production infrastructure.

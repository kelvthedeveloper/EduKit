# EduKit architecture rules

- EduKit is not SaaS and is not multi-tenant.
- Each school has an independent installation and database.
- Django owns business logic, authorization, and database access.
- Next.js must not access PostgreSQL directly.
- The local school system must support offline operation.
- The local server must not expose its database or application directly to the public internet.
- NFC card identifiers are not permanent student identities.
- Attendance must be event-based.
- Synchronization must be designed for retries, duplicate delivery, and idempotency.
- Never invent requirements or implement unrelated features.
- Add tests for new business logic as it is introduced.
- Never commit secrets or real credentials.

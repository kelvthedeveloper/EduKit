# EduKit Phase 1 Security & Architecture Verification — Specification

## Problem

Phase 1 of the EduKit School Management System implemented Identity, Authentication, RBAC, Permission Scopes, Authorization, Audit, and School-server LAN access. A verification and hardening pass is required **before** any Phase 2 (Student Management) work proceeds, to ensure the security foundation is genuinely production-ready, is compatible with the future offline/cloud dual-architecture, and does not contain exploitable vulnerabilities or architectural gaps.

## Users & Stakeholders

- System superusers / DevOps operators (cloud)
- School administrators (school-level RBAC, LAN)
- Teachers, Parents, Students (end-users of the platform)
- Future Phase 2+ module developers (need stable, documented authz primitives)

## Goals

1. Verify every claimed Phase 1 feature against the *actual* code implementation (not the previous summary).
2. Find and fix every **real** security vulnerability in authentication, session management, authorization, RBAC, audit, and deployment configuration.
3. Resolve architectural ambiguities (scope override semantics, dual Django+UserSession, identifier normalization, superuser boundaries, multi-identifier collision, revoked-session enforcement).
4. Add tests covering every discovered vulnerability and every critical security path.
5. Update documentation to describe implemented (not aspirational) behaviour and explicitly mark anything still planned.
6. Run the complete backend test suite, frontend lint/typecheck, and migration check; arrive at 0 failing tests and 0 new TS/lint errors caused by this phase.

## Non-Goals

- DO NOT implement Students, Guardians, Staff, Classes, Subjects, Admissions, Attendance, NFC, Results, Finance, Website CMS, or the Sync engine.
- DO NOT introduce new business domains.
- DO NOT perform unnecessary project restructuring.
- DO NOT write hundreds of new permissions or new scope types.
- DO NOT implement cloud/local identity synchronization (only verify UUID compatibility).

## Functional Requirements

### FR1 — Authentication lifecycle
- Login → Auth backend verifies identifier+password, rejects inactive/locked/suspended/pending accounts correctly, records failed attempts with lockout, performs timing-safe comparison for unknown identifiers.
- Session creation prevents fixation (flush old session / cycle session key), creates UserSession record with device metadata.
- Authenticated requests: session validity includes Django session expiry AND UserSession.active (not revoked, not expired).
- Session touch/refresh: updates both Django session expiry and UserSession.last_activity.
- Logout: server-side invalidates Django session and sets UserSession.revoked_at; both logout-of-current and logout-of-all must work.
- Expired/revoked sessions are rejected for subsequent authenticated requests.

### FR2 — Password security
- Passwords hashed by Django's PBKDF2/Argon2 stack; plaintext never written to logs, audit, sessions, or database (other than `password` hash column).
- Password reset tokens: cryptographically random (secrets.token_urlsafe), expire, single-use (consumed_at set), old tokens invalidated on use.
- Password reset requests do NOT leak account existence (same response for known/unknown identifiers at API boundary).
- Password reset completion invalidates all other active sessions for the user.

### FR3 — Cookie / CSRF
- `SESSION_COOKIE_HTTPONLY=True` in all environments.
- `SESSION_COOKIE_SECURE=True` in **cloud** production; in school-server the setting is environment-aware (opt-in via env, default False for pure-HTTP LAN deployments, True when HTTPS is enabled).
- `SESSION_COOKIE_SAMESITE=Lax` minimum (base config correct already).
- CSRF cookies mirror the above SAMESITE/SECURE pattern; CSRF protection enabled globally; unsafe methods POST/PUT/PATCH/DELETE require valid CSRF; **no** global CSRF disable.
- CORS: explicit `CORS_ALLOWED_ORIGINS` in every environment; no wildcard with credentials; `CORS_ALLOW_CREDENTIALS=True` paired with a concrete origins list.

### FR4 — Session model
- UserSession model supports: creation, expiration, revocation (single or all-other/all), multiple devices, last_activity, device metadata (ip/ua/device_id/name), logout, administrative revocation.
- A **Django-session-side middleware or authentication hook** ensures that revoked UserSessions cannot make authenticated requests even if the Django session cookie is still technically valid.
- Document the architectural decision for having both Django's session backend AND the UserSession model.

### FR5 — Multi-identifier login
- Login by email, phone, or username via `MultiIdentifierAuthenticationBackend` + `UserManager.get_by_identifier`.
- Email lookup case-insensitive.
- Username lookup case-insensitive with whitespace stripping.
- Phone: E.164-compatible normalization, whitespace stripping.
- Creating users normalizes identifiers so the unique database indexes actually prevent collision.
- No scenario where identifier "JohnDoe" (username) and identifier "johndoe" (same username with different case) resolve to two distinct users that can both authenticate independently.
- No scenario where a numeric username is incorrectly classified as a phone number and looks up the wrong user.

### FR6 — Account status semantics
- `ACTIVE` → login & authorized requests allowed (documented policy).
- `INACTIVE` → login denied; any existing sessions rejected (documented policy).
- `SUSPENDED` → login denied; any existing sessions rejected (documented policy).
- `PENDING_VERIFICATION` → login denied until explicitly activated or verified via password-reset-confirm flow (documented policy — current implementation upgrades PENDING_VERIFICATION→ACTIVE on password-reset-confirm; keep that behaviour and document it).
- Tests cover each state vs login.

### FR7 — RBAC enforcement
- User → RoleAssignment → Role → RolePermission → Permission(codename) → Scope → Policy.
- `AuthorizationService.can(user, permission_codename, resource)` MUST evaluate scope policy against the resource; generic permission must not grant object-level access.
- `AuthorizationService.filter_queryset(user, permission_codename, qs)` MUST return only scoped-visible rows; GLOBAL scope returns the whole set; absent permissions return `.none()`.
- Server-side enforcement is authoritative; frontend checks are UX only.

### FR8 — User role assignment security
- A user MUST NOT be able to assign themselves a role via the `UserRoleAssignmentView` (assignment target `user_uuid` vs authenticated user).
- A user MUST NOT be able to grant any permission they themselves do not already hold at GLOBAL or equivalent.
  - A teacher with `roles.manage [ASSIGNED_CLASSES]` cannot grant `finance.*`.
  - A SCHOOL_ADMIN with `roles.manage [GLOBAL]` can assign any non-system-superuser privilege.
- `SUPER_ADMIN` role (RBAC-level) AND `is_system_superuser` (Django bypass flag) are **only** assignable by an existing system superuser.
- Removing a security-sensitive role from yourself requires explicit additional protection (or simply block self-remove of the last super-admin-equivalent role).

### FR9 — Scope override semantics
- **Rule:** A `RoleAssignment.scope_override` can only NARROW (or keep equal) the effective scope vs the role's RolePermission.scope. It may never widen.
  - Example: role permission scope = `ASSIGNED_CLASSES`, override = `GLOBAL` → the override MUST be clamped/ignored; effective remains `ASSIGNED_CLASSES`.
  - role scope = `GLOBAL`, override = `SELF` → effective = `SELF` (narrowing is allowed).
  - role scope = `ASSIGNED_CLASSES`, override = `SELECTED_CLASSES` → effective = `SELECTED_CLASSES` (narrowing is allowed; parameters preserved from scope_context).
- Implement a strict "scope narrowing" function in `AuthorizationService.get_effective_permissions` with documented scope ordering.
- Add tests for allowed and forbidden override combinations.

### FR10 — Superuser security
- `User.is_system_superuser` is a BooleanField guarded from writes through:
  - `UserMeSerializer` read-only fields list (already excludes it; confirm and add test if missing).
  - A dedicated check in any identity/user update endpoint that prevents non-superusers from toggling it on others or themselves.
- `create_superuser` in UserManager sets it; ordinary `create_user` always sets it False (already).
- Django admin / shell `is_superuser` (PermissionsMixin) and custom `is_system_superuser` are clearly separated; documentation explains the two flags.
- Frontend cannot create superusers because role assignment already requires backend authorization.

### FR11 — Permission registry
- Permission codenames in `PermissionService.SYSTEM_PERMISSIONS` are stable, unique, domain-oriented, machine-readable, and independent of UI labels.
- Action choices on Permission match one of the `Action` constants; no orphaned `Action.CREATE` codename that is actually stored as e.g. `attendance.record`.
- Add a uniqueness/consistency check test.

### FR12 — Authorization test matrix
Using minimal fixtures (no student domain objects needed):
- Superuser → allowed on everything appropriate.
- Administrator (SCHOOL_ADMIN role) → allowed on assigned perms; denied on unassigned (e.g. finance.refund if not granted).
- Teacher with ASSIGNED_CLASSES on students.view → allowed for class 1 objects, denied for class 2 objects using context injection.
- Parent with OWN_CHILDREN → allowed own child id, denied others (via context children_ids injection).
- Student with SELF → allowed self, denied other user ids.
- filter_queryset equivalent variants.

### FR13 — Audit immutability & redaction
- `AuditEvent.save()` blocks updates of existing rows; `AuditEvent.delete()` blocks deletes.
- Document that QuerySet.update / .delete at manager level still bypass this (known limitation, future DB triggers / row-level security recommendation).
- `AuditService.sanitize()` redacts values for keys case-insensitively containing at least: `password`, `token`, `access_token`, `refresh_token`, `secret`, `session_key`, `api_key`, `private_key`, `authorization`; works recursively through nested dicts and lists.
- Add tests for the newly added sensitive keys (authorization, api_key, private_key, secret_key).
- Audit logins, failed logins, lockouts, role assignments, role removals, password changes, password resets.

### FR14 — Offline authentication & sync compatibility
- School server authentication chain uses only local PostgreSQL + local Redis + local Django. No calls to external identity providers / OAuth / cloud APIs in the login path.
- All critical identity-related models use `BaseModel` → UUID primary keys suitable for future cloud↔school-server synchronization:
  - User.uuid, Role.uuid, Permission.uuid, PermissionScope.uuid, UserSession.uuid, AuditEvent.uuid, RoleAssignment.uuid, RolePermission.uuid.
  - Document any missing UUID fields or non-UUID FK references that would complicate sync.

### FR15 — School server LAN network security
- Docker compose `docker-compose.school.yml`:
  - Nginx exposes LAN-reachable port (bound 0.0.0.0:80 — already correct for LAN access; NOT 127.0.0.1).
  - PostgreSQL, Redis, Celery worker, Django backend ports are NOT exposed on the host (no `ports:` entry, only inter-container links via network).
- Nginx configuration for school server:
  - proxies `/api/`, `/admin/` to backend; `/` to frontend; static/media aliased.
  - Security headers present; request size limit present; timeouts sensible; WebSocket upgrade headers on frontend proxy.
- No HTTPS in school-server nginx by default (pure LAN HTTP); document how to enable (optional TLS section + env toggle).
- Health checks on database/redis/celery do not leak credentials.

### FR16 — CORS, frontend security, API client
- Cloud CORS: env-driven explicit list (production.py already does it; confirm no wildcard + credentials).
- School server CORS: explicit list with LAN hostnames (school_server.py does it; confirm no wildcard).
- Frontend `AuthProvider` / `useAuth` / `PermissionGate`: comments and logic make it clear that UI checks are not authoritative. No tokens logged to console. 401 responses handled consistently (redirect to login, no infinite refresh loop).
- `ApiClient`: credentials=include, CSRF token read from cookie and sent on unsafe methods, 401 handled via logout flow, no token/password in any error messages or console logs.

### FR17 — Rate limiting foundation
- Login, password reset, verification endpoints have DRF throttle scopes + django-ratelimit decorators (already).
- Redis-backed `ratelimit` cache alias configured (base). School local dev falls back to locmem (already).
- Document any remaining gaps to be addressed in a later phase (e.g. per-identifier throttle rather than per-IP, distributed lockout counters).

### FR18 — Seed command
- `seed_identity --with-demo-users` continues to guard against production use: checks DEPLOYMENT_MODE + DEBUG, with an additional escape-hatch env var for QA.
- Default demo password is strong and clearly documented as dev-only.

## Non-Functional Requirements

### NFR1 — Zero new failing tests
All existing tests continue to pass. New tests cover every security fix. Final backend: 0 test failures.

### NFR2 — Frontend build quality
`pnpm lint` and `pnpm typecheck` (or the present equivalents) report 0 new TS/lint errors introduced by this phase.

### NFR3 — No migration breakage
`python manage.py makemigrations --check` reports no changes required after hardening; if code changes force migrations (e.g. adding fields), they are additive and explicitly justified. `python manage.py migrate` runs cleanly (against SQLite in dev).

### NFR4 — No cosmetic-only changes
Every file change must correspond to a real vulnerability, architectural ambiguity, test gap, or documentation inaccuracy discovered during the inspection.

### NFR5 — Traceable decisions
Architectural decisions (dual session model, scope narrowing rules, PENDING_VERIFICATION behaviour, Django vs custom superuser flags, audit immutability guarantees) are written into `docs/architecture/` and `docs/security/` files with rationale.

## Constraints & Assumptions

- Stack: Django 4.2, DRF, PostgreSQL/Redis on backend; Next.js 15 + Tailwind v4 on frontend; Docker Compose for school server; Nginx reverse proxy.
- Tests run against dev SQLite/locmem settings profile; we do not require a live Postgres/Redis for the hardening pass.
- We assume `DEPLOYMENT_MODE` env correctly selects settings modules.
- We do not implement new UI pages; frontend changes are defensive code paths and type adjustments only.

## Open Questions

None. All outstanding policy choices (scope override narrowing semantics, PENDING_VERIFICATION on password-reset, Django+UserSession dual model) will be resolved during implementation as specified above.

## Acceptance Criteria

| # | Type | Criterion |
|---|------|-----------|
| AC1 | rule | Authentication lifecycle passes security tests: login denied for INACTIVE/SUSPENDED/PENDING_VERIFICATION; lockout triggers at threshold; lockout expires; logout invalidates UserSession + Django session; revoked sessions are rejected on next authenticated request. |
| AC2 | rule | Password reset: unknown identifier returns identical API response shape as known; token cryptographically random; token single-use; token expires; password-reset-confirm revokes other sessions. |
| AC3 | rule | Multi-identifier normalization: email (case-insensitive), username (lowercase + strip), phone (E.164 normalize) all normalized on both create AND lookup; no two users can share a normalized identifier. |
| AC4 | rule | RoleAssignment.scope_override is strictly a narrowing operation; tests prove GLOBAL override on an ASSIGNED_CLASSES role does NOT grant global access. |
| AC5 | rule | Non-system-superuser cannot assign SUPER_ADMIN role, cannot toggle is_system_superuser, and cannot grant permissions outside their own effective GLOBAL set. Self-role-assignment endpoint blocks target=requesting-user for privilege changes. |
| AC6 | rule | AuthorizationService.can with resource object evaluates scope policy and denies an out-of-scope resource even when the generic permission is granted. |
| AC7 | rule | AuthorizationService.filter_queryset with ASSIGNED_CLASSES / SELF / OWN_CHILDREN scopes returns strictly filtered results; GLOBAL returns full queryset; no permissions returns none. |
| AC8 | rule | AuditEvent.save blocks updates; AuditEvent.delete blocks deletes; sanitize correctly redacts authorization, api_key, private_key, secret_key nested keys. |
| AC9 | rule | SessionSerializer in the sessions list endpoint does NOT leak session_key or refresh_token_jti to the client. |
| AC10 | rule | Cookie settings: SESSION_COOKIE_HTTPONLY=True always; SESSION_COOKIE_SECURE=True in cloud; school-server has env-aware toggle defaulting False but True if SCHOOL_SERVER_HTTPS=1. CSRF mirrors. No CORS wildcard with credentials. |
| AC11 | rule | docker-compose.school.yml: nginx port 80 bound 0.0.0.0 (LAN-reachable); postgres/redis/worker/backend have NO exposed host ports. |
| AC12 | rule | Backend test suite `pytest` passes 0 failures. |
| AC13 | rule | `makemigrations --check` reports no pending migrations at end of phase; `migrate` runs successfully under dev profile. |
| AC14 | rubric | Documentation quality — authentication, session, RBAC/permission/scope, authorization flow, superuser model, audit immutability, offline auth, LAN network, and sync UUID considerations each have dedicated sections with explicit implemented-vs-planned callouts. Scored 0..2; pass threshold ≥1.5. |
| AC15 | rubric | Workflow fidelity — spec/tasks artifacts precede approval; implementation records completion evidence per task; tests added for every fix; independent review pass written. Scored 0..2; pass threshold ≥1.5. |

# EduKit Phase 1 Security Hardening — Implementation Tasks

Priority scale: **high** = blocks readiness or is a genuine vulnerability; **medium** = architectural/documentation gap; **low** = polish.

Every task contains task-local Test Requirements (TR) typed exclusively as `rule` or `rubric`.

---

## Task 1: Install Python dev dependencies & run baseline tests

**Priority:** high
**Read-first:** [requirements.txt](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/requirements.txt), [requirements-dev.txt](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/requirements-dev.txt), [pytest.ini](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/pytest.ini)

**Objective:** Ensure we can execute pytest, django-admin, and pnpm commands end-to-end before making changes. Capture baseline.

**Work items:**
1. `pip install -r requirements-dev.txt` inside the API project.
2. Run baseline `pytest` and record pass/fail count.
3. Run `python manage.py makemigrations --check --settings=config.settings.development`.
4. Frontend: `pnpm install` at monorepo root; run `pnpm --filter @edukit/web lint` and `pnpm --filter @edukit/web build` (or equivalent) and capture errors (if any pre-existing, document).

**Test Requirements:**
- **TR1.1 (rule):** pytest executes with at least one test file discovered. Pre-existing failures are documented separately from failures introduced later.
- **TR1.2 (rule):** `makemigrations --check` runs and returns 0 or is documented as "no pending changes".
- **TR1.3 (rule):** pnpm install and frontend lint commands run (exits are noted).

**Completion Evidence:** Shell output excerpts captured in task completion section of each later task; baseline numbers recorded.

---

## Task 2: Fix identifier normalization & multi-identifier collisions

**Priority:** high
**Read-first:** [managers.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/managers.py), [user.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/models/user.py), [backends.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/backends.py)

**Objective:** Resolve three real vulnerabilities in identifier resolution:
1. Username lookup is case-sensitive → two accounts `John` and `john` both created and both loggable.
2. Phone lookup is case-sensitive, whitespace-tolerant mismatch, not normalized on write.
3. `_identifier_type` misclassifies numeric-only usernames (e.g. `1234567`) as phone → looks up wrong field → can authenticate the unintended account.

**Work items:**
1. In `UserManager._identifier_type`, require phone to have either leading `+` OR have E.164-like length >= 9 AND contain no letters; also add a sanity threshold so <=6 digit strings are classified as `username`, not `phone`.
2. Add `normalize_identifier(identifier) -> (type, normalized)` helper that:
   - email: lowercases + strips whitespace (existing `normalize_email`).
   - username: lowercases + strips whitespace.
   - phone: strips whitespace/dashes/parens; keeps leading `+`; digits only after `+`.
3. In `get_by_identifier`, use the normalized form: email via `email__iexact`, username via `username=normalized` (but `User.clean`/save must normalize first; or use case-insensitive __iexact), phone via normalized match (and save must normalize too).
4. In `User.clean()` (or in `_create_user` pre-save), actually write normalized email/username/phone to the DB so the unique indexes apply to normalized forms.
5. Ensure at least one non-null identifier field is required at validation time.

**Test Requirements:**
- **TR2.1 (rule):** Creating `username="John"` and then `username="john"` raises an IntegrityError / ValidationError on the second save.
- **TR2.2 (rule):** `get_by_identifier("JohnDoe")` returns the same user as `get_by_identifier("johndoe ")` when username stored lowercase = "johndoe".
- **TR2.3 (rule):** `get_by_identifier("123456")` (6 digits) resolves to username lookup, not phone.
- **TR2.4 (rule):** Phone "+233 12 345 6789" and "+233123456789" are stored identically and both resolve to the same user.

---

## Task 3: Fix session fixation + revoked session enforcement

**Priority:** high
**Read-first:** [authentication.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/services/authentication.py), [session.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/services/session.py), [session model](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/models/session.py), [permissions/__init__.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/permissions/__init__.py)

**Objective:**
1. Fix session fixation: explicitly call `request.session.flush()` before `django_login()` to cycle the session key (Django's `login()` may cycle but we want it explicit and testable).
2. Add middleware or DRF authentication layer that checks `UserSession.revoked_at` for the current session_key and forces logout if revoked.
3. Fix `LogoutView` session_key handling (it calls `django_logout` first, so session_key is lost before `SessionService.revoke_by_session_key`).

**Work items:**
1. In `AuthenticationService.login(request, user)`: call `request.session.flush()` first; then `django_login(request, user)`; then proceed.
2. In `AuthenticationService.logout(request)`: capture session_key BEFORE `django_logout(request)`; pass it to `SessionService.revoke_by_session_key`.
3. Create `identity/middleware.py` with `SessionRevocationMiddleware`. On each request that has an authenticated user AND a session, load the corresponding `UserSession` (by session_key, active, not revoked, not expired). If no matching active UserSession exists → call `django_logout(request)`, return 401 or let middleware continue as anonymous (choose safe logout).
4. Register the new middleware in `base.py` settings after `AuthenticationMiddleware`.
5. Also update `SessionService.touch_session` to extend `expires_at` when the session is touched.

**Test Requirements:**
- **TR3.1 (rule):** After calling `AuthenticationService.login`, the UserSession.revoked_at == None and Django session exists.
- **TR3.2 (rule):** After calling `SessionService.revoke_by_session_key`, a subsequent request using that Django session is treated as unauthenticated by the middleware.
- **TR3.3 (rule):** Logout captures and revokes the UserSession before Django logout clears the cookie.

---

## Task 4: Fix SessionSerializer session_key leak

**Priority:** high
**Read-first:** [authentication.py serializers](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/serializers/authentication.py)

**Objective:** `SessionSerializer` currently exposes `session_key` and (via model fields) potentially `refresh_token_jti` to any authenticated user calling the sessions list endpoint. These are authentication secrets.

**Work items:**
1. Remove `session_key`, `refresh_token_jti` from `SessionSerializer.Meta.fields`. Keep uuid, user_uuid, device fields, ip, auth_source, last_activity, expires_at, revoked_at, created_at.
2. Keep `LoginResponseSerializer` clean (it already only returns session_uuid, not the raw Django key — confirm).

**Test Requirements:**
- **TR4.1 (rule):** `SessionSerializer(instance).data.keys()` does not contain `session_key` or `refresh_token_jti`.

---

## Task 5: Fix scope override ESCALATION (narrowing-only rule)

**Priority:** high
**Read-first:** [authorization.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/permissions/services/authorization.py), [constants/__init__.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/common/constants/__init__.py)

**Objective:** The current `scope_code = override_scope_code or rp.scope.code` allows an `ASSIGNED_CLASSES` role permission to silently become `GLOBAL` if the user's assignment has a `scope_override=GLOBAL`. This is **privilege escalation**.

**Work items:**
1. Define a scope hierarchy ordering in constants: `GLOBAL > DEPARTMENT > ASSIGNED_CLASSES/ASSIGNED_SUBJECTS/SELECTED_CLASSES > OWN_CHILDREN > SELF`. (GLOBAL is widest; SELF is narrowest.)
2. In `AuthorizationService.get_effective_permissions`, compute `effective_scope = min_privilege(role_scope, override_scope)` where `min_privilege` returns the narrower one. If `override_scope` is wider than (or incomparable but wider than) the role scope, **drop** the override and keep role_scope. Log a warning.
3. Write helper `narrower_scope(scope_a, scope_b, scope_order)` returns the narrower.
4. Scope parameters merging: keep role's scope_parameters if override is none; if override is narrower, merge parameters (override wins for the narrower scope).

**Test Requirements:**
- **TR5.1 (rule):** Permission with role_scope=ASSIGNED_CLASSES + override=GLOBAL → effective_scope remains ASSIGNED_CLASSES.
- **TR5.2 (rule):** Permission with role_scope=GLOBAL + override=SELF → effective_scope becomes SELF (narrowing allowed).
- **TR5.3 (rule):** Permission with role_scope=ASSIGNED_CLASSES + override=SELECTED_CLASSES → effective_scope=SELECTED_CLASSES (allowed, comparable narrowing).
- **TR5.4 (rule):** AuthorizationService.can returns False for an out-of-scope student object even when override tried to widen to GLOBAL.

---

## Task 6: Harden role assignment (self-assignment, privilege escalation, SUPER_ADMIN boundary)

**Priority:** high
**Read-first:** [permission_views.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/permissions/views/permission_views.py), [role_service.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/permissions/services/role_service.py), [authorization.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/permissions/services/authorization.py)

**Objective:**
1. Block role assignment where `target_user == actor` for any privilege-increasing operation (can still decrease? safer: block entirely for consistency, document).
2. Implement a "can-assign-role" check in RoleService: actor must already hold at GLOBAL scope every permission that the target role grants (i.e., the actor cannot grant a permission they don't already hold globally).
3. Block revocation of the last system-superuser-equivalent role (to prevent lockout).
4. Block setting scope_override that widens the resulting permission (use Task 5's helper).
5. Prevent `IsAccountActive` from being bypassed.

**Work items:**
1. In `RoleService.assign_role`:
   - If `assigned_by` is the same user as `user`, raise `PermissionDenied('Self-service role assignment is not permitted.')`.
   - Compute `target_role_effective_permissions` (the permissions that the role grants).
   - If `assigned_by` is not system_superuser, verify `assigned_by` holds each permission at GLOBAL scope (via AuthorizationService.can with resource=None). If any permission is missing → PermissionDenied.
   - Enforce scope override narrowing via Task 5 rules before saving.
2. In `RoleService.remove_role`:
   - If the role being removed is the last SUPER_ADMIN or last role giving is_system_superuser-like access, and no other system superusers exist, block.
   - If `assigned_by == user` and role is SUPER_ADMIN / is_system_superuser role, log an audit warning and require a second superuser.
3. In `RoleViewSet.create/update_role`:
   - A non-system-superuser cannot create or update a role whose resulting permissions include things the creator does not hold at GLOBAL scope.
4. Keep the existing SUPER_ADMIN system_superuser gating check (already exists in `UserRoleAssignmentView`).
5. Prevent users from modifying their own account_status or is_system_superuser via `MeView.patch`. (Already, `UserMeUpdateSerializer` only allows first/last/display_name — confirm; add defensive test.)

**Test Requirements:**
- **TR6.1 (rule):** `assign_role(user=teacher, role=SUPER_ADMIN, assigned_by=teacher)` → PermissionDenied (self-assignment).
- **TR6.2 (rule):** A SCHOOL_ADMIN without `finance.refund GLOBAL` cannot assign BURSAR role (which includes finance.refund).
- **TR6.3 (rule):** A SYSTEM_SUPERUSER can assign any role; assignment succeeds.
- **TR6.4 (rule):** Attempting to attach scope_override=GLOBAL to a TEACHER role that has students.view@ASSIGNED_CLASSES → effective remains ASSIGNED_CLASSES, no escalation.
- **TR6.5 (rule):** `MeView.patch` with `account_status=SUSPENDED` or `is_system_superuser=true` has no effect (fields ignored, 400 or safe no-op).

---

## Task 7: Environment-aware cookie security settings

**Priority:** medium
**Read-first:** [base.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/config/settings/base.py), [school_server.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/config/settings/school_server.py), [production.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/config/settings/production.py)

**Objective:**
1. Keep `SESSION_COOKIE_HTTPONLY=True` always (base).
2. Production cloud: already `SESSION_COOKIE_SECURE=True` + `CSRF_COOKIE_SECURE=True` ✓.
3. School server LAN: currently both SECURE flags are absent (default False). Add env-aware toggle: `SCHOOL_SERVER_HTTPS=1` → set both SECURE True; otherwise keep default False.
4. Verify no `CORS_ALLOW_ALL_ORIGINS = True` exists anywhere (grep).
5. Double-check SESSION_COOKIE_SAMESITE and CSRF_COOKIE_SAMESITE are at least Lax everywhere (base correct).

**Work items:**
1. In `school_server.py`:
   ```python
   _school_https = os.environ.get('SCHOOL_SERVER_HTTPS', '').lower() in ('1','true','yes','on')
   SESSION_COOKIE_SECURE = _school_https
   CSRF_COOKIE_SECURE = _school_https
   ```
2. Grep codebase for `CORS_ALLOW_ALL_ORIGINS`, `CSRF_TRUSTED_ORIGINS = ["*"]` and remove any wildcard if present.

**Test Requirements:**
- **TR7.1 (rule):** `importlib`-based test or live-Django settings check confirms school_server with SCHOOL_SERVER_HTTPS=1 has SECURE=True; with unset has SECURE=False.
- **TR7.2 (rule):** production settings always have SECURE=True.
- **TR7.3 (rule):** No file matches `CORS_ALLOW_ALL_ORIGINS\s*=\s*True` in the Django settings tree.

---

## Task 8: Audit sensitive key expansion + queryset bypass warning

**Priority:** medium
**Read-first:** [audit_service.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/audit/services/audit_service.py), [constants/__init__.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/common/constants/__init__.py)

**Objective:**
1. Expand `AUDIT_SENSITIVE_KEYS` to include all of: `password`, `token`, `access_token`, `refresh_token`, `secret`, `secret_key`, `api_key`, `private_key`, `authorization`, `session_key`, `cookie`, `csrf`, `jwt`.
2. Add audit tests for the new keys (nested dict and lists).
3. Document in docs/security/audit.md the QuerySet.update/.delete bypass limitation and recommend future PostgreSQL row-level security or REVOKE UPDATE/DELETE on the audit table for the app role.

**Work items:**
1. Update `AUDIT_SENSITIVE_KEYS` in constants.
2. Add unit tests for new keys and nested variants.

**Test Requirements:**
- **TR8.1 (rule):** `AuditService.sanitize({"Authorization": "Bearer xxx"})["Authorization"] == "[REDACTED]"`.
- **TR8.2 (rule):** `AuditService.sanitize({"config": {"api_key": "sk-xxx", "private_key": "...", "public_key": "ok"}})` → only `api_key` and `private_key` REDACTED; `public_key` preserved.

---

## Task 9: Add authorization matrix + account_status tests

**Priority:** high
**Read-first:** existing tests in [test_authentication.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/tests/test_authentication.py), [test_authorization.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/permissions/tests/test_authorization.py)

**Objective:** Add tests covering:
- Login allowed/denied matrix for ACTIVE, INACTIVE, SUSPENDED, PENDING_VERIFICATION.
- Authorization matrix for superuser, admin, teacher (assigned classes), parent (own children), student (self).
- Object-level `can()` and `filter_queryset()` with in-scope/out-of-scope resources using context injection (children_ids, assigned_class_ids etc.).
- Revoked middleware behaviour (Task 3).

**Work items:**
1. Create new backend tests under identity/tests and permissions/tests as needed; extend existing files.
2. Use `AuthorizationService.can` with context parameters for scope policy checks when domain objects don't yet exist.
3. Add a `test_pending_verification_denied_login_then_activated_by_password_reset` case.

**Test Requirements:**
- **TR9.1 (rule):** ACTIVE→login succeeds; INACTIVE, SUSPENDED, PENDING_VERIFICATION→login fails.
- **TR9.2 (rule):** Authorization matrix tests: superuser passes every can() check; admin passes own, fails finance.refund when not in role; teacher passes class A student, fails class B student via context; parent passes own child ID, fails other; student passes self ID, fails other.
- **TR9.3 (rule):** filter_queryset returns only in-scope rows for each role context.

---

## Task 10: Verify docker-compose.school.yml LAN exposure

**Priority:** medium
**Read-first:** [docker-compose.school.yml](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/docker-compose.school.yml), [school-server nginx default.conf](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/infrastructure/nginx/school-server/default.conf)

**Objective:** Guarantee school-server LAN architecture has exactly one ingress (Nginx port 80) and databases/workers are internal-only.

**Work items:**
1. Review `services.nginx.ports`: confirm `"80:80"` which binds 0.0.0.0 → LAN reachable. Do not change this unless it binds 127.0.0.1 only.
2. Ensure `postgres`, `redis`, `backend`, `worker` services have **no** `ports:` section. If present, remove. (Current compose appears correct; verify.)
3. Add healthcheck endpoint safety comment. Nginx config: ensure `/static` and `/media` exist; increase timeouts if necessary; add a plaintext env comment that school-server HTTPS requires extra cert volume + TLS listen block.

**Test Requirements:**
- **TR10.1 (rule):** Only `nginx` has a `ports:` key in the school compose; all others rely on Docker internal DNS.
- **TR10.2 (rule):** nginx listen is 80 with server_name _; proxies /api and /admin to backend, / to frontend.

---

## Task 11: Seed command hardening & demo safety

**Priority:** medium
**Read-first:** [seed_identity.py](file:///c:/Users/Brah%20Progrez/Documents/GitHub/EduKit/apps/api/apps/identity/management/commands/seed_identity.py)

**Objective:** Make the demo-user safety gate more robust.

**Work items:**
1. Gate reads as: `if options['with_demo_users']: if (settings.DEBUG is False and os.environ.get('ALLOW_DEMO_USERS_IN_NONDEBUG') != '1'): raise CommandError`.
2. Document the env override for QA.
3. Confirm all demo accounts use `email_verified=True`, `account_status=ACTIVE`, and password is strong default with clear dev-only warning.

**Test Requirements:**
- **TR11.1 (rule):** Running seed with `--with-demo-users` under non-DEBUG raises unless override env set. (We test this by running call_command in test with DEBUG=False monkeypatch.)

---

## Task 12: Update documentation

**Priority:** medium
**Read-first:** existing files under `docs/security/` and `docs/architecture/`.

**Objective:** Realign docs with actual implementation. Current authentication.md mentions JWT as primary, but actual implementation uses Django sessions (with JWT SimpleJWT available only as alternate auth class). Document both, explain session model as primary.

**Work items:**
1. Rewrite `docs/security/authentication.md`:
   - Actual strategy: Django-session-cookie + UserSession audit/revocation model.
   - Login lifecycle (including fixation protection, revocation, touch, logout).
   - Multi-identifier login (email/phone/username normalization rules).
   - Lockout policy: attempts, duration, reset on success.
   - Password reset: token properties, single-use, expiry, account-existence concealment, other-session invalidation.
   - PENDING_VERIFICATION vs ACTIVE/INACTIVE/SUSPENDED behaviour.
   - Implemented vs planned (MFA, SSO not yet done).
2. Rewrite `docs/security/authorization.md`:
   - User → RoleAssignment → Role → RolePermission → Permission → Scope → Policy chain.
   - Scope hierarchy rule and override narrowing semantics.
   - Object-level enforcement via can() and filter_queryset().
   - Superuser model: `is_system_superuser` (Django level system bypass, non-grantable via RBAC APIs) vs Django `is_superuser` on PermissionsMixin (admin panel) vs role-based SUPER_ADMIN (school-level GLOBAL on all configured perms).
3. Rewrite `docs/security/audit.md`:
   - Append-only guarantee at application level.
   - Known bypass: QuerySet.update / .delete; DB-level recommendation (REVOKE, row-level security).
   - Redaction rules (sensitive keys list).
4. Create/Update `docs/architecture/school-server.md`:
   - Single ingress nginx:80.
   - Internal-only containers (postgres/redis/worker/backend).
   - TLS optional with SCHOOL_SERVER_HTTPS env toggle + cert volume instructions.
   - Offline authentication: no external dependencies in login path.
   - UUID-based identifiers on all identity models for future cloud/school-server sync. List any model that does NOT yet have a uuid sync-ready identifier (RolePermission, RoleAssignment — check; they inherit BaseModel, good).
5. Create `docs/architecture/sessions-and-scopes.md` explaining the dual Django session + UserSession model rationale and scope override narrowing semantics.

**Test Requirements:**
- **TR12.1 (rubric):** Documentation completeness and accuracy. Scored 0..2; pass threshold ≥1.5. Dimension: does each document explicitly call out implemented-vs-planned, and accurately reflect the code?

---

## Task 13: Install, run backend tests, migrations check

**Priority:** high
**Objective:** Final pipeline run.

**Work items:**
1. `pip install -r requirements-dev.txt` (if not yet done).
2. `python manage.py makemigrations --check --settings=config.settings.development`.
3. `python manage.py migrate --settings=config.settings.development`.
4. `python -m pytest --tb=short -v` and record 0 failures from our test set.

**Test Requirements:**
- **TR13.1 (rule):** makemigrations --check exit 0.
- **TR13.2 (rule):** migrate completes without errors.
- **TR13.3 (rule):** pytest exit 0, 0 failed.

---

## Task 14: Frontend lint + typecheck

**Priority:** medium
**Objective:** Ensure frontend has no regressions introduced by our backend changes (normally none; but run commands as required by the brief).

**Work items:**
1. `pnpm install` at root.
2. `pnpm --filter @edukit/web lint`.
3. `pnpm --filter @edukit/web build` or tsc typecheck equivalent.

**Test Requirements:**
- **TR14.1 (rule):** Any pre-existing TS/lint errors are documented with line numbers; zero NEW errors introduced by this phase.

---

## Task 15: Independent review pass & final report

**Priority:** high
**Objective:** A separate read-only pass (implementer self-review if no independent agent available, but recorded as Review step in Spec Mode) that checks each AC against the evidence list, then writes the final 12-section security report as required by item 30 of the brief.

**Work items:**
1. Walk every AC in spec.md and link to evidence (tests written, files changed, docs updated).
2. Write final_report.md under the spec folder with:
   1. Security findings (CRITICAL/HIGH/MEDIUM/LOW/INFO list)
   2. Changes made (files + why)
   3. Authentication decision
   4. RBAC decision chain
   5. Scope override semantics
   6. Superuser security
   7. Audit guarantees
   8. Offline authentication
   9. LAN exposure matrix
   10. Test results (commands + outputs summary)
   11. Known limitations
   12. Phase 2 readiness conclusion (READY / NOT READY)

**Test Requirements:**
- **TR15.1 (rule):** Every item in security findings references a concrete file or test evidencing the issue and fix.
- **TR15.2 (rule):** Phase 2 readiness verdict is NOT READY if any CRITICAL or HIGH issue remains unfixed.

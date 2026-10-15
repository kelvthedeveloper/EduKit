# EduKit database design review

**Review status:** Design review only. This document does not approve implementation.  
**Sources reviewed:** `database-design-proposal.md` and `school-requirements-checklist.md`.  
**Scope:** Requirements traceability, relationship/lifecycle gaps, MariaDB readiness, decisions, and a future implementation sequence. No credentials were read; no database was queried.

## 1. Summary

The proposal covers the major required domains and uses sound foundations: explicit relational tables, history-oriented records, `BIGINT UNSIGNED` identifiers, InnoDB/`utf8mb4`, decimal money, UTC event instants, restricted deletion, and transaction boundaries. It is not yet ready to translate directly into migrations.

The main blockers are school policies already called out in the checklist, plus several technical details that need tightening before schema work:

- A year-specific section, subject offering, placement, assessment, mark, and daily attendance record need enforceable links to the same student, class/section, and academic period. Separate foreign keys alone do not ensure those values agree.
- The `classes`/`sections` division is still ambiguous and may duplicate the grade-level concept.
- Student/staff/guardian login links are individually optional one-to-one links, but the proposal does not state whether one account may link to more than one kind of person.
- Event idempotency, manual attendance sources, correction/recalculation precedence, and cross-person event references need precise rules.
- Grading needs a frozen configuration and an explicit authoritative source for a mark after revisions and publication.
- Refunds, reversals, receipt reissues, and allocation changes need a single, non-overlapping accounting effect. The proposal describes their intent, but not yet how balances are calculated for every combination.
- Some stated uniqueness rules cannot be implemented as written with nullable columns in MariaDB, and several cross-row rules cannot be guaranteed by ordinary foreign keys or unique indexes alone.

Resolve all Critical school policy decisions and the technical items marked critical in section 4 before approving migrations. Optional tables/features should remain optional; the proposal is not an instruction to build every listed table in the first release.

## 2. Requirements coverage

Coverage means the proposal has a plausible domain home; it does **not** mean the policy is settled or the relationship is implementation-ready. “Critical before migrations” identifies decisions or integrity rules needed before defining the affected schema.

### 2.1 Checklist traceability

| Checklist requirement | Proposed domain/tables | Coverage and remaining gap | Critical before migrations? |
|---|---|---|---|
| 1.1 Educational levels | `education_levels`, `grade_levels` | Covered structurally; actual levels, grade names, ordering, and whether a campus/program needs a separate scope remain unknown. | Yes |
| 1.2 Class/stream names | `classes`, `sections`, `grade_levels` | Partial: terms “class”, cohort, homeroom, and section may overlap. Confirm the school’s real structure; decide whether `classes` adds a concept beyond grade and section. | Yes |
| 1.3 Mid-year class changes | `student_enrollments`, `enrollment_placements` | Covered by effective-dated placements; rule for dates, approval, overlap, and whether subject groups differ from homerooms remains open. | Yes |
| 1.4 Promotion/repetition | `student_enrollments`, `enrollment_placements` | Covered as new-year enrollment and placement history; decision criteria, repeat/promotion status, and correction flow need school policy. | Yes |
| 1.5 Transfers/withdrawals | `admissions`, `student_enrollments`, `enrollment_placements` | Partial: lifecycle and effective dates are described, but transfer-in/out and withdrawal statuses/reasons/destination data are not fully specified. | Yes |
| 2.1 Year start/end | `academic_years` | Covered; dates, naming, overlap/revision policy remain open. | Yes |
| 2.2 Terms/semesters | `academic_terms`, `assessment_periods` | Covered; number/type, dates, and whether all levels share them need confirmation. | Yes |
| 2.3 Different level calendars | `academic_years`, `academic_terms`, `education_levels` | Partial: no direct proposed relationship scopes calendar to a level/program. Confirm whether separate calendars are needed; otherwise year/term may be school-wide. | Yes |
| 2.4 Changes to published dates | `academic_years`, `academic_terms`, `audit_logs` | Partial: history/audit is generally proposed, but date revisions/versioning and approval are not specified. | Yes |
| 3.1 Student-number format/reuse | `students.student_number` | Covered as unique business ID; format, scope, assignment authority, normalization, and non-reuse policy remain open. | Yes |
| 3.2 Admission information | `admissions`, `students`, `student_documents` | Partial: table purposes exist, but exact required/optional/sensitive fields and collection timing must be agreed and minimized. | Yes |
| 3.3 Applicant-to-student transition | `admissions.student_id`, `students` | Partial: the proposal explicitly asks when a student row is created; duplicate applications and acceptance/linking rules need definition. | Yes |
| 3.4 Guardian/contact requirements | `guardians`, `student_guardians` | Covered for many-to-many relationships; contact types, primary/emergency status, custody/consent restrictions, and one-primary enforcement need decisions. | Yes |
| 3.5 Student/guardian logins | `users`, `students.user_id`, `guardians.user_id`, `user_roles` | Covered as optional logins; portal scope, shared-account prohibition, and whether accounts can be linked across person categories remain open. | Yes for account relationship; portal features can defer if out of scope |
| 3.6 Existing student data import | Student/admission/guardian tables; migration/import process | Import is a school question, not a proposed table. Source, quality, matching, and historical depth affect keys and rollout. | Yes before production data migration |
| 4.1 Arrival/departure procedures | `attendance_sources`, `attendance_events`, daily attendance tables | Covered structurally; source locations, directions, sessions, and scan timing rules need confirmation. | Yes |
| 4.2 Forgotten/lost card | `id_cards`, manual attendance/corrections | Partial: revocation/replacement exists; temporary-card and identity-verified manual procedures are not defined. | Yes for initial attendance workflow |
| 4.3 Duplicate/incorrect scans | `attendance_events`, daily attendance, `attendance_corrections` | Partial: event history and idempotency are proposed, but duplicate window/key and correction approval/recalculation rules are not settled. | Yes |
| 4.4 Late/early rules | Daily attendance and rule configuration (not yet inventoried as a dedicated table) | Partial: computed status is proposed, but thresholds/calendar/session rules are not modeled concretely. Decide whether configuration is stored or versioned in application settings. | Yes |
| 4.5 Attendance correction authority | `attendance_corrections`, `users`, `roles`, `audit_logs` | Covered in concept; permissions, approval, actor attribution, and correction append-only semantics need decisions. | Yes |
| 4.6 Staff attendance | `staff_daily_attendance`, `staff_employments` | Optional by proposal; school must decide whether to include in the first attendance schema. | Yes if in first release; otherwise can defer |
| 4.7 Outage behavior | Sources/events; local operations | Partially covered as offline/LAN objective, but scanner buffering, event ordering, trusted time, retries, and reconciliation during server outages are unspecified. | Yes for attendance-device design |
| 4.8 Cards/devices | `id_cards`, `attendance_sources`, `attendance_events` | Covered hardware-independently with opaque tokens; card population/lifecycle, source authentication, payload format, and device capability remain open. | Yes for card/attendance implementation |
| 5.1 Components and weights | `assessment_components`, `assessment_types` | Covered as configurable components; weight units, normalization, level/subject scope, and whether a component can span multiple terms need confirmation. | Yes |
| 5.2 Grading scope variation | `grading_schemes`, `grading_bands` | Covered in concept; overlapping scope precedence and relation to class-subject/assessment type need a deterministic selection rule. | Yes |
| 5.3 Boundaries/rounding/pass | `grading_schemes`, `grading_bands` | Covered as configurable values; inclusive/exclusive bounds, score range, rounding stage/mode, and pass requirements remain open. | Yes |
| 5.4 Absences/missing marks | `student_marks.status` | Partial: separate statuses are recommended, but the allowed statuses and calculation treatment must be specified. | Yes |
| 5.5 Resits/corrections | `student_marks`, `mark_revisions`, `published_results` | Covered in concept; attempt eligibility, which attempt counts, correction approval, and post-publication handling remain open. | Yes |
| 5.6 Rankings/ties | `published_results` | Partial: ranking is an unresolved policy and no rank snapshot/algorithm is specified. It can be omitted if not needed. | Yes if required at launch; otherwise defer |
| 5.7 Result approval/publication | `published_results`, `users`, `mark_revisions`, `audit_logs` | Covered in concept; approval roles, publication state transitions, republishing, and recipient visibility need confirmation. | Yes |
| 5.8 Report-card format/history | `published_result_subjects`; protected generated artifact suggested | Partial: result snapshot is proposed, but report content, signatures/comments, and whether exact rendered copies must be retained are unknown. | Content yes; exact PDF artifact can defer |
| 6.1 Fee types/timing | `fee_categories`, `fee_schedules`, `fee_schedule_items` | Covered structurally; category list, due dates, recurring periods, and late charges remain open. | Yes |
| 6.2 Fee variation | `fee_schedules` applicability | Partial: year/level/grade/section scope is proposed, but individual charges/optional services and precedence across scopes are unresolved. | Yes |
| 6.3 Discounts/scholarships/waivers | `invoice_adjustments` | Partial: adjustments are proposed but entitlement, calculation basis, approval, and whether these apply before or after invoicing need policy. | Yes |
| 6.4 Partial/multi-invoice payments | `payments`, `payment_allocations` | Covered in concept; allocation can be many-to-many, but proposed unique `(payment_id, invoice_id)` blocks multiple separate allocations for one pair. Confirm whether aggregation per pair is sufficient. | Yes |
| 6.5 Overpayments/unapplied credit | `payments`, allocations | Explicitly unresolved; credit-on-account is not fully modeled as a liability/credit ledger. | Yes |
| 6.6 Refunds/corrections | `payment_refunds`, `payment_reversals`, `invoice_adjustments` | Partial: separate records exist, but effect/order against allocations, invoice balance, receipt, and accounting totals is ambiguous. | Yes |
| 6.7 Receipt numbering/printing | `receipts` | Covered in concept; numbering scope, reprint vs replacement, void rules, paper requirements, and sequence concurrency need confirmation. | Yes |
| 6.8 Finance roles | `users`, `roles`, `permissions`, `audit_logs` | Covered in concept; separation of duties, limits, and approval matrix need school confirmation. | Yes |
| 6.9 Existing finance import | Financial tables and import process | Import is not otherwise designed; opening balances, unpaid invoices, receipts, and reconciliation source must be decided. | Yes before finance data migration |
| 7.1 Reports by role | Domain tables; report definitions not proposed as tables | Requirements are requested, but report inventory/filter/export requirements are not modeled yet. Most reports can be queries; specific snapshots/retention may require design. | Critical reports yes |
| 7.2 View/change permissions | `roles`, `permissions`, `user_roles`, `role_permissions` | Covered as role-based access; row scope (assigned class/student/subject) is not modeled by these tables alone. Confirm whether access is global or scoped. | Yes |
| 7.3 Guardian portal | `guardians.user_id`, `student_guardians`, `users` | Relationship foundation exists; guardian-specific authorization and permitted data/actions remain open. Portal can be deferred if no first-release requirement. | Yes if portal is in first release |
| 7.4 Retention | Audit, documents, attendance, finance histories | Partial: retention is a policy question; retention/anonymization and legal holds affect deletion, partitioning, and storage. | Yes |
| 7.5 Backups | `backup_runs`, protected backup files | Covered operationally in concept; RPO/RTO, frequency, retention, encryption, offline copy, restore permissions/testing need decisions. | Backup policy before launch; table can defer |
| 8.1 Currency | Fee schedules, invoices, payments, adjustments/refunds | Money columns and explicit currency are proposed; official currency, minor-unit precision, rounding, and multi-currency needs remain open. | Yes |
| 8.2 Timezone | School settings and UTC instants/local dates | Recommended UTC + school-local interpretation; actual IANA zone and per-campus differences remain open. | Yes |
| 8.3 Local-only requirements | Architecture and source/device model | LAN/no routine internet is confirmed, but outage behavior and any features depending on remote services need inventory. | Yes for launch-critical operations |
| 8.4 Hardware/PA | `attendance_sources`, `id_cards`; PA explicitly deferred | Scanner integration is vendor-independent in concept. Existing hardware constraints need confirmation; PA schedule/announcements/hardware can be designed later unless required at launch. | Scanner/device constraints yes; PA can defer |

## 3. Relationship and lifecycle review

### 3.1 Academic years, classes, sections, enrollment

- **Potential duplication:** `grade_levels` already represents the ordered educational step, while `classes` is described as a named cohort “derived from a grade” and `sections` as a year-specific stream. For some schools, class means grade; for others it means homeroom. Keeping all three without the school’s vocabulary can duplicate the same concept or make reports join through an artificial layer. Confirm whether the actual structure is grade → year-specific section, or grade → cohort/class → section.
- **Year mismatch risk:** `sections.class_id` and `sections.academic_year_id` do not ensure the class’s grade and academic-year relationships are valid (and the section has no direct grade FK). `class_subjects.academic_term_id` may point to a term from a different year than its section. A simple FK checks each referenced row, not that the related years agree.
- **Nullable unique behavior:** `class_subjects` proposes uniqueness on `(section_id, subject_id, academic_term_id)` while `academic_term_id` is nullable. MariaDB permits multiple `NULL` values in a unique index, so “one offering without a term” is not enforced. Decide whether every offering belongs to a term, use a separate year-level offering plus term-specific records, or use a normalized non-null scope.
- **Enrollment/placement consistency:** A placement can currently reference an enrollment for one student/year and a section for another year; separate FKs do not prevent that. The design should ensure year alignment and should model an enrollment with no current placement if the process allows it, then add historical placements as they are assigned. The proposal diagram's `||--|{` placement suggests every enrollment must always have a placement, which conflicts with admissions, pending placement, or withdrawn-before-class cases.
- **Promotion and overlaps:** Effective dates preserve history, but a unique key does not prevent two active/overlapping placements for the same enrollment. Define whether a same-day handover is allowed and enforce overlap with a locked transactional operation plus tests. `academic_years`/terms can also overlap; the proposed date index does not prevent overlap.
- **Subject/class alignment:** Assessment components reference a `class_subject` and marks separately reference an enrollment. Nothing in the listed FKs proves that enrollment was placed in the offering's section for that period, or even belongs to that academic year. Resolve eligibility rules and enforce them in the service/transaction, potentially with composite keys/relationships.
- **Timetable gap:** Timetables and timetable entries are named in the academic-structure requirement in the proposal’s source brief, but there are no timetable tables or an explicit decision to defer them. Decide whether timetable scheduling is in scope for the first academic release. If included, it depends on sections, class-subject offerings, rooms, staff assignments, and effective periods; avoid adding it before those rules are known.

### 3.2 Student, guardian, staff, and login account links

- The one-to-one optional `user_id` on students, guardians, and staff prevents two accounts for one profile, but does **not** prevent the same `users.id` from being linked once to a student, once to staff, and once to a guardian. Confirm whether a single person with multiple school relationships should use one login or separate accounts; then choose one explicit account-person model and constraints.
- `student_guardians` treats a student/guardian pair as unique, which cannot retain two distinct relationship episodes for the same pair without revising or versioning the row. Clarify whether relationship changes/custody history must be retained, and whether a guardian may have separate contact permissions per child.
- Primary guardian is only an application rule. If the schema stores a boolean, concurrent updates can leave two primary contacts. Use a transactional reassignment and a database-enforceable strategy appropriate to the selected MariaDB version.
- `admissions.student_id` nullable supports pre-admission applications, but the unique application number does not address duplicate applications for the same person or link/merge rules. Define whether multiple applications and reapplications are allowed.
- `staff` is stable identity and `staff_employments` stores episodes, which is a sound separation. `teaching_assignments` points to `staff`, not a particular employment episode, so an assignment could overlap employment or remain active after employment ends. Decide whether that is valid; otherwise reference/validate employment and year/term alignment.
- The Mermaid diagram uses optional one-to-one notation for account relationships, but it does not communicate whether a user can be associated across person types. Tighten this before account data is seeded.

### 3.3 Cards and attendance

- Card replacement/revocation is represented, but “at most one active card per person” is left as a question. A unique index on nullable `(student_id, status)` is not sufficient to enforce one active card across statuses reliably. Define overlapping active-card rules and use an explicit active-card key or transactional constraint.
- `attendance_events` includes both a nullable `id_card_id` and nullable student/staff IDs. Those columns could identify different people unless the service validates them together. An FK cannot ensure a scanned card belongs to the recorded person. Likewise, raw device event time could predate card issue or postdate revocation; decide whether the event is rejected, retained as rejected evidence, or accepted based on scan time vs server receipt time.
- A revoked card's FK is useful history, but validation must happen at event time. Do not resolve only against the card's current status when replaying already accepted events.
- The raw event's disposition may be mutable if a later process updates duplicate/accepted status, conflicting with the “immutable event” rule. Prefer an immutable received event plus separately append-only processing decisions, or define a one-time immutable disposition and insert a separate duplicate-attempt event.
- A unique nullable `(source_id, external_event_id)` allows multiple null IDs in MariaDB; it only deduplicates devices that provide a stable ID. An idempotency key must be generated consistently and retained across retries. A time-window duplicate rule is separate from request idempotency and must not discard legitimate arrival/departure events.
- `attendance_source_id` is required even for manual entry; manual staff attendance may not come from a device. Define a controlled manual source/source type and actor, or model manual corrections separately. Do not forge a scanner source.
- Daily-record event FKs do not guarantee that the event belongs to the same student/staff, date/session, direction, or school day. The correction table's exactly-one daily target check also does not ensure before/after content is valid for that target. The service must validate these invariants transactionally and retain actor/reason.
- “Manual attendance”, “manual correction”, rejected scans, and scanner replay are distinct operations. Define how each affects the calculated daily row and how a later reprocessing run respects approved corrections.
- If devices queue scans while the server is down, decide durable device storage, authenticated sync, ordering, trusted clock drift, duplicate retries, and reconciliation. “LAN/offline” at application level does not automatically provide device-side offline capture.

### 3.4 Assessment and published results

- `assessment_periods` can reference both a year and optional term independently; no FK ensures the term belongs to that year. Similarly a component can connect a period to a class-subject offering from another year/term.
- `student_marks` can connect a student enrollment to a component for a different section/year. Define eligibility at mark-entry and publication, and enforce it in the transaction.
- Weight scope is ambiguous: component weights may belong to a subject/period, assessment type, year, class, or education level. A `DECIMAL` weight field is not enough without a documented denominator/normalization rule and validation.
- Marks have both a mutable-looking current row and an append-only `mark_revisions` history. Define which is authoritative, whether every edit writes a revision atomically, and how an originally entered mark is preserved. A publication snapshot should identify the exact mark revisions/configuration version used.
- `grading_schemes` scopes are nullable and can overlap. The proposal acknowledges precedence but leaves it open; do not let “most specific wins” emerge accidentally from query order. Confirm a deterministic selection rule or require exactly one applicable version per result.
- Versioned schemes are only safe if a published result's scheme and component/aggregation configuration cannot be edited in place. Freeze/version all inputs (not only the grade band) and retain the calculation inputs or a reproducible snapshot.
- Missing/absent/exempt statuses need explicit calculation behavior; `mark=NULL` must not ambiguously mean all of these. Also define whether a resit replaces, caps, or coexists with earlier attempts.
- Published subject rows refer to current `class_subjects`; changes to subject name/offerings could affect report reproduction. Snapshot display labels and required breakdowns if historical report consistency matters.
- Ranking is unresolved and should not be modeled as an ordinary mark. If required, define population (class/level/year), tie handling, visibility, and whether rank is frozen at publication.

### 3.5 Finance

- Currency, scale, rounding, fee applicability precedence, tax/penalty rules, and numbering scopes are Critical decisions. `DECIMAL` is correct, but `DECIMAL(p,s)` and currency code must be picked from actual maximums and currency minor units.
- `payment_allocations` unique `(payment_id, invoice_id)` conflicts with the possibility of multiple allocation entries for one payment/invoice pair (e.g. separate allocation/reallocation history). Either one current aggregate row with append-only allocation changes, or multiple rows with an allocation identifier/reversal lifecycle; do not leave it as an “unless” choice in a migration.
- Allocation reductions/reassignments have no explicit allocation-reversal/reallocation table. Editing/deleting a posted allocation would undermine financial history. Add an approved compensating allocation event or an explicit allocation history mechanism after policy is decided.
- `payment_refunds` and `payment_reversals` can overlap for one payment. Their amounts, state transitions, and effects on allocations, receipts, payment totals, and invoice balances are not defined. A full reversal after a partial refund could double-count returned funds. Choose one authoritative movement model and define allowed transitions and constraints.
- The balance explanation says to derive invoice balance from lines, adjustments, allocations, reversals, and refunds, but a refund does not necessarily restore an invoice receivable (for example, a goodwill refund vs an erroneous payment). Define adjustment vs payment refund semantics. Document exact formulas and reconciliation invariants before implementation.
- `payment_reversals` links to a payment but does not explicitly link to reversed allocations or a receipt. `invoice_adjustments` says reversal is a linked compensating adjustment, but no self-reference/reversal link is listed. Receipts mention replacement but no prior/replacement FK is listed. Model these explicit links if the school requires traceable correction chains.
- `payments.student_enrollment_id` is optional, while allocations connect to invoices that identify an enrollment. This allows a payment not attributable to a student until later. Confirm whether this supports general/unapplied credit, payer attribution, and later allocations; otherwise require a payer/student record.
- Payment/receipt numbering, cash/manual payment references, same-day duplicate reference scope, reprints, voids, and stale invoices need concurrency-safe policies. Uniqueness of a final string alone does not define how the next number is allocated.
- Schedule item, invoice line, adjustment, refund, and payment amounts need sign conventions. If adjustments are required to be positive, the effect direction must come from a constrained adjustment type. Avoid negative and positive conventions that can be mixed silently.
- `fee_schedule_items` can be changed after invoices reference them. Preserve posted invoice snapshots and prohibit editing/deleting effective schedule versions after use.

### 3.6 Audit, backup, privacy, offline

- `audit_logs.entity_type/entity_id` is intentionally polymorphic and has no FK; this can be acceptable for a cross-domain audit stream, but the ID may refer to a deleted/mistyped entity. Preserve domain rows, validate entity type against an allowlist, and make audit entries append-only. If database-level referential integrity is mandatory, use domain-specific audit links or a separate auditable-event reference design.
- `user_roles` is described with optional grantor and effective intervals but unique `(user_id, role_id)` only permits a single row for all time. That is compatible with one current grant plus audit history, but effective dates and revocation need precise semantics; do not retain old grant rows with the same unique pair.
- Actor `SET NULL` conflicts with auditability unless the event snapshots durable actor identity (without unnecessary personal data) or user accounts are deactivated rather than deleted. Prefer no hard deletion of accounts once they have acted.
- `backup_runs` records activity but is not a backup system. Restore procedures, immutable/offline copy, encryption, retention, and tests must be operational requirements; a table cannot ensure a backup is restorable.
- Privacy and retention must distinguish records that cannot be deleted for financial/legal history from personal data that may need correction/anonymization. Define policies by record type and legal jurisdiction.
- Offline operation is covered at a high level. Local asset hosting is compatible, but device clock reliability, timezone-data updates, backup media, software updates, and any remote reporting/notification dependencies require operational answers.

## 4. MariaDB readiness and decision register

**Status meanings:** `Awaiting school confirmation` is a policy question; `Technical recommendation pending` is a developer/architect choice awaiting review; `Ready for approval` means the review recommends a default, but it still needs explicit sign-off before migrations.

### 4.1 School policy questions

| ID | Plain-language decision | Why it matters | School respondent | Priority | Status |
|---|---|---|---|---|---|
| S-01 | Confirm educational levels, grade names, class/stream meanings, homerooms, subject groups, and whether campuses/programs differ. | Determines whether `classes` is necessary and the core class/section relationships. | School head, academic staff | Critical | Awaiting school confirmation |
| S-02 | Confirm year, term/semester structure, date ranges, per-level calendar differences, holidays, and how published dates may change. | Defines academic scopes and prevents cross-year term/assessment/fee links. | School head, administrator, academic staff | Critical | Awaiting school confirmation |
| S-03 | Confirm student-number format, assignment authority, uniqueness scope, and whether numbers may ever be reused. | Sets durable unique identifiers and import/matching rules. | Administrator | Critical | Awaiting school confirmation |
| S-04 | Confirm application lifecycle: when an applicant becomes a student, whether repeat applications are allowed, and how duplicates/merges are handled. | Determines admission-to-student relationships and unique application constraints. | Administrator | Critical | Awaiting school confirmation |
| S-05 | Confirm student profile fields, required/sensitive admission information, documents, and collection timing. | Minimizes personal data and determines record/document scope. | Administrator, school head | Critical | Awaiting school confirmation |
| S-06 | Confirm guardian relationships, emergency contacts, primary contact, custody/consent restrictions, and relationship history. | Determines relationship attributes, visibility, and whether contacts need historical episodes. | Administrator, school head | Critical | Awaiting school confirmation |
| S-07 | Confirm whether students/guardians need accounts and portal features; may one account serve a person who is also staff/guardian? | Decides account links, authorization boundaries, and potential cross-person identity. | School head, administrator | Critical if accounts in initial release | Awaiting school confirmation |
| S-08 | Confirm student-year enrollment cardinality and promotion, repetition, transfer, withdrawal, midyear placement changes, approvals, and effective dates. | Determines uniqueness and temporal placement constraints. | School head, academic staff, administrator | Critical | Awaiting school confirmation |
| S-09 | Confirm arrival/departure locations, sessions/cutoffs, late/early rules, repeated scans, forgotten-card/manual entry, correction permissions, and approval. | Defines daily attendance calculation and correction lifecycle. | School head, administrator, attendance lead | Critical | Awaiting school confirmation |
| S-10 | Confirm attendance during server/network outage: device queuing, paper fallback, later entry, required timing/order, and clock trust. | May require device sync IDs, queued-event reconciliation, and distinct received/event times. | Administrator, IT/device lead | Critical | Awaiting school confirmation |
| S-11 | Decide whether staff attendance is in the first attendance release. | Adds a second person/employment daily-attendance path. | School head, administrator | Important | Awaiting school confirmation |
| S-12 | Confirm ID card populations, issue/expiry/replacement procedure, scanners/hardware already owned, and device event-ID support. | Determines card constraints and source integration requirements. | Administrator, IT/device lead | Important | Awaiting school confirmation |
| S-13 | Confirm assessments, weights, grading scope, boundaries, rounding stage, pass rules, missing/absent/exempt behavior, resits, and mark corrections. | Determines assessment configuration and result calculation model. | Academic staff, school head | Critical | Awaiting school confirmation |
| S-14 | Confirm result approvals/publication, post-publication correction, ranking/tie policy, and report-card content/history. | Defines publication versions, authorization, and required snapshots. | School head, academic staff | Critical | Awaiting school confirmation |
| S-15 | Confirm fee categories, fee schedule scopes/due dates, optional services, adjustments, scholarships, discounts, waivers, penalties, and approvals. | Determines fee schedule applicability and financial adjustments. | Accounts officer, school head | Critical | Awaiting school confirmation |
| S-16 | Confirm partial payments, allocation across invoices, unapplied credit/overpayments, payer attribution, and allocation changes. | Determines whether credit balances and allocation history are needed. | Accounts officer, school head | Critical | Awaiting school confirmation |
| S-17 | Confirm refunds, payment corrections/full or partial reversal, receipt void/reissue/copy rules, numbering scope, and reference uniqueness. | Prevents double-counting and establishes immutable transaction lifecycles. | Accounts officer, school head | Critical | Awaiting school confirmation |
| S-18 | Confirm official currency, any other currencies, maximum transaction/invoice amounts, and rounding rules. | Selects decimal precision, currency storage, and calculation constraints. | Accounts officer, school head | Critical | Awaiting school confirmation |
| S-19 | Confirm school timezone and whether campuses share it; specify school-day boundary if not ordinary midnight. | Determines UTC conversion and school-local reporting dates. | School head, administrator | Critical | Awaiting school confirmation |
| S-20 | Confirm required reports by role, including statutory outputs, filters, exports, rankings, finance reconciliation, and history. | Reports may change retained snapshots, indexes, and data fields. | Administrator, academic staff, accounts officer | Critical for required reports | Awaiting school confirmation |
| S-21 | Confirm role permissions and whether users are restricted to assigned classes/students/subjects, plus approval separation/limits. | Global roles alone do not model row-level authorization scope. | School head, administrator | Critical | Awaiting school confirmation |
| S-22 | Confirm retention, archival, anonymization/deletion, legal holds, document retention, and rejected scan retention. | Affects preservation, privacy, deletion rules, and operational storage. | School head, administrator, accounts officer | Critical | Awaiting school confirmation |
| S-23 | Identify existing student, guardian, staff, attendance, grades, and financial data sources and required import history. | Drives identifiers, matching, migration staging, and reconciliation acceptance. | Administrator, accounts officer, data owner | Critical before import | Awaiting school confirmation |
| S-24 | Confirm backup frequency, retention, off-site/offline copy, restore permissions, and acceptable data-loss/downtime window. | Determines operational backup controls; `backup_runs` alone is insufficient. | School head, administrator, IT lead | Important before launch | Awaiting school confirmation |
| S-25 | Confirm local-only operating requirements, LAN users, internet-dependent exceptions, and any hardware integration needed at launch. | Determines offline availability boundaries and operational design. | School head, administrator, IT/device lead | Critical for launch scope | Awaiting school confirmation |
| S-26 | Confirm whether timetable scheduling is needed in the first release and what class/subject/teacher/room/time rules apply. | Timetable is in the source-domain scope but absent from the proposed table inventory. | Academic staff, administrator | Important; Critical if launch feature | Awaiting school confirmation |

### 4.2 Technical design decisions (recommendations, not approvals)

| ID | Technical question / recommended default | Why it matters | Reviewer | Priority | Status |
|---|---|---|---|---|---|
| T-01 | Use the stated conventions: InnoDB, `utf8mb4`, `BIGINT UNSIGNED` surrogate IDs, `snake_case`, named FKs/indexes, and explicit unique business IDs. | Consistent types and predictable migrations; aligns with project requirements. | Developer / database reviewer | Important | Ready for approval |
| T-02 | Choose one MariaDB-supported `utf8mb4` collation after checking the Ubuntu server's MariaDB version and required search behavior; do not rely on server defaults. | Collation differences can change uniqueness and search results across development/production. | Developer / database reviewer | Important | Technical recommendation pending |
| T-03 | Store instants in UTC `DATETIME(6)`; store school-calendar dates as `DATE`; set application/database session timezone deliberately and convert using a confirmed IANA school zone. | Prevents host-local time and MariaDB session conversion from changing dates. | Developer / database reviewer | Critical | Technical recommendation pending |
| T-04 | Store currency code with posted financial facts and choose `DECIMAL(p,s)` only after school confirms currency minor units and maximums; never use floating point. | Ensures historical amounts remain interpretable and calculations exact. | Developer / accounts reviewer | Critical | Technical recommendation pending |
| T-05 | Do not rely on ordinary FKs for equality across multiple relationships. Add composite candidate keys/FKs where practical; otherwise enforce year/student/section/event consistency in one transactional service with concurrency tests. | Prevents individually valid FKs from linking incompatible records. | Developer / database reviewer | Critical | Technical recommendation pending |
| T-06 | Resolve nullable unique keys explicitly. Require a non-null period/scope key or split the offering tables; MariaDB permits multiple NULLs in unique indexes. | Prevents duplicate no-term class-subject offerings and ambiguous uniqueness. | Developer / database reviewer | Critical | Technical recommendation pending |
| T-07 | Keep raw scans, posted invoices/payments, mark revisions, and published results immutable; use append-only correction/reversal events and ensure one authoritative current projection. | Avoids silent history loss and conflicting current-vs-revision values. | Developer / database reviewer | Critical | Ready for approval |
| T-08 | Define payment/refund/reversal/allocation effects as a transaction ledger or a single event model before DDL; require reconciliation invariants for invoice due, payment received, allocated amount, refunded amount, and reversals. | Avoids a refund and reversal both reducing the same balance or allocation history being overwritten. | Developer / database reviewer with accounts officer | Critical | Technical recommendation pending |
| T-09 | Use atomic sequence allocation for student/invoice/receipt IDs only if the school needs sequential numbers; never derive a number from `MAX(id)+1`; make numbering scope explicit. | Avoids duplicate numbers under concurrent requests and number reuse after voids. | Developer / database reviewer | Critical | Technical recommendation pending |
| T-10 | Prefer one explicit account-to-person relationship model that prevents one account from being linked to unrelated profiles unless multi-role identity is deliberately supported. | Current three nullable `user_id` FKs do not prevent cross-type or shared-account ambiguity. | Developer / security reviewer | Critical if portal/account links are in scope | Technical recommendation pending |
| T-11 | Keep composite audit entity references only if entity type is allowlisted and records are preserved; retain actor attribution without hard-deleting users. | A polymorphic audit reference cannot receive a normal FK. | Developer / security reviewer | Important | Technical recommendation pending |
| T-12 | Start without partitioning or cached balances; add only after query/volume evidence. Keep reports query-driven where historical snapshots are not required. | Reduces operational complexity for a small school and MariaDB deployment. | Developer / database reviewer | Can defer | Ready for approval |
| T-13 | Specify immutable scanner event ID/idempotency behavior and separate request-retry idempotency from “looks like a duplicate scan” policy. | A unique key alone cannot deduplicate devices that submit no stable event identity. | Developer / device integrator | Critical for attendance | Technical recommendation pending |
| T-14 | For future migrations, use ordered additive migrations, one migration-history table with checksum/applied timestamp, and separate migration credentials from the web runtime account. | Supports repeatable releases and least privilege; avoid circular FKs by adding optional late FKs in later migrations. | Developer / database reviewer | Important | Ready for approval |

## 5. MariaDB readiness assessment

| Topic | Assessment |
|---|---|
| Primary/foreign keys | `BIGINT UNSIGNED` and explicit FKs are appropriate. Clarify one-to-one account semantics and add relationship consistency rules for year, section, student, event, and term. Use `RESTRICT` for historical records and avoid account/person cascade deletion. |
| Unique constraints/indexes | The proposal lists useful access indexes, but some constraints are conditional or ineffective as written: nullable term unique keys allow duplicates; unique payment/invoice pairs preclude multiple allocation entries; nullable external IDs do not deduplicate scans without IDs; one-active-card and one-primary-guardian constraints need a MariaDB-compatible strategy. Confirm all business identifier scopes and case/normalization rules. |
| Monetary values | `DECIMAL` is required and correct. Precision/scale, currency minor units, rounding, negative-value semantics, and multi-currency treatment remain unapproved. Define transaction-level totals and checks before DDL. |
| Date/time | UTC `DATETIME(6)` instants plus local `DATE` is a sound recommendation, not an approved timezone. Configure database/application session timezone explicitly. Device event time, receive time, and school attendance day must remain distinct. |
| Transactions | Proposed boundaries are appropriate. Define lock order and invariants for payment allocation, receipts, promotion/placement, scan ingestion/reprocessing, grading publication, and corrections. Make retries idempotent and limited to known transient failures. |
| History | Enrollment placements, raw scans, mark revisions, result versions, invoices, payments, and reversals are intended to retain history. Resolve mutable current rows vs append-only revisions/projections and ensure configuration versions used for published results/invoices are frozen. |
| Deletion/correction | `RESTRICT`, deactivation/revocation, and compensating records are appropriate. Define anonymization/retention for personal information, immutable actor attribution, and exact links from a correction/reversal to the original. |
| Migration ordering | The proposal identifies an order and key cycles. Resolve `school_settings.updated_by_user_id` to users created later (add the FK later or defer it), create classrooms before sections, users before actor FKs, years before terms/sections, and offerings before teacher assignments/assessment components. Avoid cross-domain FKs that create cycles. |
| MariaDB-specific behavior | Confirm production MariaDB release before choosing `CHECK`, generated columns, partial/filtered uniqueness workarounds, JSON use, and collation. Do not assume nullable unique semantics act like filtered unique indexes. Avoid unsupported partial indexes; use normalized keys or transaction-enforced rules where necessary. |

## 6. Recommended future implementation sequence

This sequence is conditional on scope approval; it does not mean every optional table must be delivered immediately.

1. **Confirm operational defaults and migration approach.** Select supported MariaDB version/collation, confirmed timezone/currency, naming conventions, migration runner/history, least-privilege migration/runtime accounts, backup/restore method. No domain schema should precede approval of these defaults.
2. **School and academic foundation.** Create school profile/settings, academic years/terms, education levels/grades, and only the approved class/section model. Add classrooms only if used. Then subjects and class-subject offerings. Resolve the active-year FK cycle by adding the optional setting FK after academic years exist.
3. **Identity and access foundation.** Create users, roles, permissions, association tables, and audit conventions before sensitive workflows. Decide and constrain account-to-person linking; keep role-scope assignments out until the school confirms scoped authorization.
4. **People and admissions.** Create students, admissions, guardians, relationship links, staff, and optional departments. Add optional user FKs after both users and person tables exist. Add protected document metadata only for confirmed document types/retention.
5. **Employment, enrollment, placement, and teaching.** Create staff employment episodes, yearly student enrollment, historical placements, then class-subject teacher assignments. Enforce same-year/same-section rules and no overlapping active placement/assignment according to policy.
6. **Cards and attendance.** Create card and source records, then immutable scan/idempotency evidence, daily student records, corrections, and optionally staff daily records. Validate manual entry, outage buffering/synchronization, and event-to-person/date consistency before accepting hardware traffic.
7. **Assessment and grading.** Create assessment types/periods/components and immutable/versioned grading configuration; then marks/revisions and publication snapshots. Ensure offerings and enrollment eligibility are validated before marks and results are published.
8. **Finance catalogue and billing.** Create fee categories/schedule versions/items, then invoices/lines and adjustments. Freeze posted lines and define numbering, scope precedence, and balance formula.
9. **Payments and settlement.** Create payments and whichever allocation-history model is approved; then receipts, refunds, and reversal/compensation records. Implement these only after accounts staff approve allocation, refund, correction, and reconciliation examples.
10. **Operational tables and performance.** Add backup-run audit only if operational ownership is defined. Add targeted indexes from actual reports and query plans; defer partitioning/cached projections until measured need. Notifications and PA/bell remain separate future work.

Each phase should include migration tests on the target MariaDB version, FK/unique/concurrency tests, representative import/reconciliation tests, and a rollback/restore plan. Do not create migrations while Critical decisions or integrity models remain unresolved.

## 7. Approval gate

### Must be resolved before schema implementation

- School terminology and academic model: levels, grade/class/section, calendars, year/term boundaries, placement and transfer lifecycle.
- Student IDs, admission conversion/duplicates, required profile data, guardian/contact relationships, import sources.
- Attendance sessions/cutoffs, arrival/departure and late rules, duplicate/idempotency behavior, manual correction authority, outage behavior, and whether staff attendance/cards are in the initial release.
- Assessment weighting and scope, grade boundaries, rounding, absent/missing marks, resits, correction/publication approvals, required reports/rankings.
- Fee applicability, currency/precision, payments/allocation/unapplied credit, discounts/waivers, receipts, refunds/reversals, numbering, approval roles, and finance imports.
- School timezone, permissions and record-level scope, privacy/retention, and launch-critical backup/offline requirements.
- Technical resolution for class/section model, cross-record year/section constraints, account-person cardinality, nullable unique keys, attendance immutability/idempotency, immutable grading inputs, and a single reconciled financial correction model.
- Confirm whether timetable scheduling, student/guardian portal, departments, staff attendance, and other optional inventory items belong in the first release.

### Can safely be deferred when excluded from launch scope

- PA/bell hardware, schedule, announcements, and schema.
- Guardian/student portal functionality if the school explicitly excludes it initially.
- Staff attendance if it is explicitly excluded from the first release.
- Departments, detailed timetable scheduling, notifications, and optional document types if not needed at launch.
- Ranking if not required; exact historical rendered report files if data snapshots suffice.
- Partitioning, cached balances, advanced report optimizations, and large-scale throughput tuning until measurements justify them.
- Import of historical data not required for launch, while preserving enough stable identifiers and opening-balance decisions for any later import.

**Approval statement:** This review identifies design gaps and recommendations only. **Creating database migrations or implementing any schema is not approved by this review.** Wait for school answers and explicit developer approval before generating schema files.

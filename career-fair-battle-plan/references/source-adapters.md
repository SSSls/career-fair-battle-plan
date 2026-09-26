# Source adapters and evidence scope

Use `normalize_source.py` to convert supplied or visible artifacts into evidence records. Visibility can change by school, account, date, registration state, and platform experiment; describe what was observed, not what the platform universally exposes.

## Adapters

- `official_school`: official university event page. It may prove event identity/date and named employers, but a featured list or login wall is incomplete.
- `handshake_public_preview`: visible employer cards, title snippets, work-authorization text, and advertised session counts. It is `PUBLIC_PREVIEW`; it does not prove a complete roster, exact JD, current slot, or registration availability.
- `handshake_authenticated`: user-opened logged-in tab with explicit `READ_ONLY` authorization. Record only visible employer, exact-role, and exact-session facts. Registration state is independent from authentication state.
- `external_role_research`: official employer career pages plus properly labeled government or secondary sources. Company history never substitutes for exact-role sponsorship.

Uploads, PDFs, screenshots, CSV exports, and copied text are `UPLOAD` artifacts and need an `artifact_reference`. LinkedIn-visible pages and other public job boards are public research inputs, not proof of hidden account content.

## Evidence record

Each claim has a unique `claim_id`, claim text, `scope`, `field`, `status`, source URL or artifact reference, publisher/quality where available, publication date when available, access date, and freshness.

Scopes: `event`, `employer_event_card`, `company_current`, `company_history`, `exact_role`, `exact_session`.

Fields: `employer`, `role`, `sponsorship`, `headcount`, `salary`, `eligibility`, `session`.

Strongest evidence levels: `EMPLOYER_NAME`, `EMPLOYER_CARD`, `TITLE_ONLY`, `EXACT_ROLE`, `SESSION_VERIFIED`. Wording cannot upgrade scope.

Always report coverage as visible count, advertised count when known, and `complete`. If a login wall, partial list, stale page, or conflict exists, coverage is not complete and absent employers cannot be treated as absent from the fair.

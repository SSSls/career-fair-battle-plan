# Research and event ingestion

Read this reference when the input includes Handshake, a fair website, employer pages, job boards, booth schedules, sessions, or sponsorship research.

## Accepted inputs

Use the strongest available read-only path:

1. user-supplied export, CSV, PDF, screenshot, or copied event text;
2. public event and employer URLs;
3. an authenticated browser tab the user has made available, limited to visible/read-only navigation. This is mandatory for live Handshake retrieval.

For the full access gate and login boundary, read [intake-and-access.md](intake-and-access.md). Do not bypass authentication, reverse-engineer private endpoints, evade access controls, or claim access to hidden Handshake jobs. When login/session access is unavailable, ask for an export or mark the data unavailable.

## Two-stage research

Avoid deep research across every exhibitor.

1. Normalize employer names, role titles, session data, and explicit eligibility constraints.
2. Apply cheap relevance filters using the approved area set and hard constraints.
3. For plausible employers, find the top one to three relevant roles.
4. Deep-research only those `company × role` pairs.

Deduplicate equivalent roles and cache unchanged pages by normalized URL plus access date.

## Source hierarchy

Prefer sources in this order:

1. exact current job posting and official event/session page;
2. company careers, university recruiting, immigration, or policy page;
3. government data;
4. reputable secondary reporting;
5. anecdotal sources, used only as labeled context.

Historical H-1B or PERM records show past activity, not that a current role sponsors. A company-wide statement does not override an exact role-level restriction.

Treat active headcount and salary as separate claims. A live job page proves that a posting exists, not that a team has confirmed remaining HC. Prefer an explicit current employer statement for `headcount.status=confirmed`. Prefer the official exact-role salary range; label company-wide ranges and secondary estimates, and never use them as hard disqualifiers.

## Claims and dates

For every material claim capture the data-contract fields. `published_at` may be null; `accessed_at` may not. Use `unknown` when a page is silent, a role has expired, or sources conflict without a reliable resolution. Record conflicts explicitly.

## Sessions and actions

- `verified`: the current source visibly confirms time/status.
- `unverified`: a secondary or stale source reports it.
- `full`: the current source visibly shows no availability.
- `unknown`: unavailable or not checked.

Also derive `visit_access` across all usable channels. A full 1:1 can still have `visit_access=verified` when a booth or group session is confirmed. When no usable channel is available, set `visit_access=unavailable`; when unresolved, set `unknown`. Record verified fixed sessions as start/end minutes relative to the fair start so deterministic code can detect conflicts.

Never turn `unknown` into an instruction to register. Propose checking availability. Even when a slot is visibly available, ask for confirmation immediately before registration, waitlisting, messaging, emailing, or applying.

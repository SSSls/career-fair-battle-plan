# Intake and access gate

Read this reference before collecting candidate or fair data, especially when the event is behind Handshake or another school login.

## Candidate intake

Collect enough information to separate demonstrated fit, user preference, and hard constraints:

- CV or equivalent experience/project material;
- school, degree, major or program, and graduation date;
- internship, co-op, or full-time target;
- desired areas, intended pivots, and areas to avoid;
- current work authorization and whether present or future sponsorship is required;
- location and relocation limits;
- salary minimum and whether it is a hard constraint;
- importance of verified active headcount;
- fair name, date, timezone, format, and source.

Do not infer sponsorship need, salary floor, or career preference from nationality, school, major, or prior work. The user must approve the profile before ranking.

## Three source modes

1. `UPLOAD`: user-supplied CSV, PDF, screenshots, export, or copied text.
2. `PUBLIC_WEB`: public event, employer, role, and session pages.
3. `AUTHENTICATED_READ_ONLY`: a browser tab where the user has logged in and explicitly authorized visible, read-only inspection for the fair.

For a live Handshake source, always require login and treat the effective mode as `AUTHENTICATED_READ_ONLY`, even when an event page appears publicly reachable. `PUBLIC_WEB` remains valid for non-Handshake sites. A user-supplied Handshake export is `UPLOAD` and does not require login.

For authenticated access, ask the user to open the site and log in themselves. Never request, receive, persist, or repeat a password; never handle MFA codes, solve CAPTCHAs, bypass access controls, or discover hidden private endpoints. Limit navigation to visible employer, role, and session information.

Registration, waitlisting, messaging, applying, uploading a CV, editing a profile, or any other mutation requires separate confirmation immediately before that action. Read-only authorization does not authorize mutations.

## Deterministic gate

Create an intake JSON document and run:

```bash
python3 scripts/assess_intake.py intake.json -o intake_status.json
```

Possible states:

- `PROFILE_REVIEW`: profile is incomplete or not explicitly approved;
- `NEED_FAIR_SOURCE`: obtain an upload, public URL, or user-opened authenticated tab;
- `NEED_USER_LOGIN`: pause while the user logs in themselves;
- `NEED_READ_ONLY_AUTHORIZATION`: ask permission to inspect the visible tab;
- `READY_FOR_INGESTION`: ingest only the available data and preserve gaps as `unknown`.

An incomplete company list or missing role/session details may still be ingested, but the gaps must remain visible and cannot be converted into positive evidence.

## Intake JSON shape

```json
{
  "candidate_profile": {
    "approved": true,
    "cv_present": true,
    "school": "Example University",
    "degree": "MS",
    "graduation_date": "2027-05",
    "role_types": ["internship"],
    "target_areas": ["backend-swe"],
    "needs_sponsorship": true,
    "work_authorization": "F-1 OPT eligible",
    "locations": ["New York"],
    "salary": {"minimum": 100000, "currency": "USD", "hard_constraint": false},
    "headcount_importance": "high"
  },
  "fair": {
    "name": "Example Fair",
    "platform": "handshake",
    "date": "2026-10-01",
    "timezone": "America/New_York",
    "format": "virtual",
    "url": "https://example.edu/fair",
    "source_mode": "AUTHENTICATED_READ_ONLY",
    "company_list_present": true,
    "role_data_present": false,
    "session_data_present": true
  },
  "access": {
    "user_logged_in": true,
    "authorization_scope": "read_only",
    "credentials_shared": false
  }
}
```

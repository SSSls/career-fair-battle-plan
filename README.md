# Career Fair Battle Plan

[English](README.md) | [简体中文](README.zh-CN.md)

An open-source Codex skill that helps job seekers allocate limited career-fair time across employers, exact roles, and sessions. It supports career changes, adjacent-field moves, sponsorship constraints, uncertain target areas, and both virtual and in-person events.

## What it optimizes

The project answers **“Where should I spend my limited fair time?”**, not merely “Should I apply?” It produces four auditable outcomes:

- `MUST_VISIT`
- `IF_TIME`
- `APPLY_ONLINE`
- `SKIP`

## Architecture

- **LLM/Codex:** understands the résumé, builds a user-approved profile, summarizes evidence, and writes human-facing guidance.
- **TypeSafe Jev:** returns atomic typed Choice, Score, and Noul judgments when live API access and a callable integration are configured.
- **Deterministic Python:** applies hard constraints, weights, confidence gates, evidence integrity, fair capacity, and schedule conflicts.
- **Read-only browser access:** inspects visible authenticated Handshake pages after the user logs in. It never handles passwords, MFA, or CAPTCHAs.

## Current scope

The implemented authenticated source is Handshake. Public web pages and user-supplied exports, screenshots, PDFs, CSV files, and copied text are also supported as evidence sources.

LinkedIn, school recruiting portals, and employer ATS sites may be researched through visible public pages or user-authorized browser access, but this repository does **not** currently include dedicated LinkedIn, school-portal, or ATS adapters. It also does not automate registration, messages, applications, or other account mutations.

## Requirements

Choose requirements based on how you want to use the project:

| Use case | Required | Optional |
| --- | --- | --- |
| Install and invoke the workflow in Codex | ChatGPT desktop with Codex, Codex CLI, or Codex IDE extension with Skill support | Git, if cloning instead of downloading ZIP |
| Run deterministic intake/ranking scripts | Python 3.10 or newer | Git |
| Research public employer and job pages | A Codex environment with web access | Uploaded fair exports or screenshots |
| Read a live Handshake fair | A Handshake account, a browser surface Codex can inspect, and user-granted read-only authorization | Existing company/session export |
| Run live Jev judgments | Current TypeSafe/Jev access, a valid `TYPESAFE_API_KEY`, and a callable Jev integration | None for the deterministic demo |
| Develop and validate this repository | Python 3.10+, Git | PyYAML plus Codex's `skill-creator` validator for package validation |

The runtime scripts use only the Python standard library. There is no required `pip install` step for `assess_intake.py`, `rank_battle_plan.py`, the scenario matrix, or the unit tests.

## Installation

### Option A — Install as a Codex skill

This is the recommended path when you want Codex to guide the full workflow: candidate intake, profile approval, evidence research, typed judgments, deterministic ranking, and the final fair-day plan.

#### A1. Install with Codex's Skill Installer

In a Codex conversation, invoke the built-in installer and ask it to install this repository:

```text
$skill-installer Install the career-fair-battle-plan skill from https://github.com/SSSls/career-fair-battle-plan.
```

Review the source when prompted. Codex normally detects installed Skills automatically; if it does not appear, restart Codex. See the [official OpenAI Skill documentation](https://learn.chatgpt.com/docs/build-skills) for current discovery and installation behavior.

#### A2. Manual user-wide install on macOS or Linux

Codex discovers personal Skills under `$HOME/.agents/skills`. Clone the repository, then symlink the inner Skill folder:

```bash
git clone https://github.com/SSSls/career-fair-battle-plan.git
cd career-fair-battle-plan
mkdir -p "$HOME/.agents/skills"
ln -s "$PWD/career-fair-battle-plan" \
  "$HOME/.agents/skills/career-fair-battle-plan"
```

The symlink keeps the installed Skill connected to the clone, so a later `git pull` updates it. If you prefer a standalone copy, replace the `ln -s` command with:

```bash
cp -R "$PWD/career-fair-battle-plan" "$HOME/.agents/skills/"
```

#### A3. Manual user-wide install on Windows PowerShell

```powershell
git clone https://github.com/SSSls/career-fair-battle-plan.git
Set-Location career-fair-battle-plan
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse -Force ".\career-fair-battle-plan" "$HOME\.agents\skills\"
```

Restart Codex if the Skill does not appear after copying it.

#### A4. Repository-scoped install

Use this when the Skill should only be available inside one project. From the target repository root:

```bash
mkdir -p .agents/skills
cp -R /absolute/path/to/career-fair-battle-plan/career-fair-battle-plan \
  .agents/skills/career-fair-battle-plan
```

Codex scans `.agents/skills` from the current working directory through the repository root.

#### A5. Install without Git

1. Open the [GitHub repository](https://github.com/SSSls/career-fair-battle-plan).
2. Select **Code → Download ZIP** and extract it.
3. Copy the extracted inner `career-fair-battle-plan` folder—the one containing `SKILL.md`—to `$HOME/.agents/skills/career-fair-battle-plan`.
4. Restart Codex if the Skill does not appear automatically.

Downloading a ZIP gives you a snapshot. To update it later, download a new ZIP and replace only that installed Skill directory.

#### Verify the Skill installation

Start a new Codex conversation and explicitly invoke:

```text
$career-fair-battle-plan
```

Then try:

```text
$career-fair-battle-plan Help me prepare for a career fair. First collect my CV,
school, target roles, sponsorship needs, constraints, and fair source. Stop for my
profile approval before researching or ranking companies.
```

A correct installation should load the workflow and begin with intake. It should not ask for a password or claim that registration or an application has been completed.

### Option B — Run the deterministic tools without installing the skill

Use this mode for local testing, CI, custom integrations, or when another agent already produces the required JSON contracts.

```bash
git clone https://github.com/SSSls/career-fair-battle-plan.git
cd career-fair-battle-plan
python3 --version
python3 -m unittest discover -s tests -v
```

Run the included ranking example:

```bash
python3 career-fair-battle-plan/scripts/rank_battle_plan.py \
  career-fair-battle-plan/examples/sample_input.json \
  -o battle_plan.json
```

Run the 57-scenario matrix:

```bash
python3 career-fair-battle-plan/scripts/run_scenario_matrix.py \
  career-fair-battle-plan/examples/scenario_matrix.json \
  -o scenario_matrix_results.json
```

These commands exercise deterministic policy and ranking. They do not read a résumé, browse a fair, call Jev, or create external actions by themselves.

Complete copy/paste smoke test (commands intentionally shown on one line):

```bash
python3 career-fair-battle-plan/scripts/assess_intake.py career-fair-battle-plan/examples/sample_input.json
python3 career-fair-battle-plan/scripts/run_scenario_matrix.py career-fair-battle-plan/examples/scenario_matrix.json
python3 /Users/sunchunxuan/.codex/skills/.system/skill-creator/scripts/quick_validate.py career-fair-battle-plan
```

The validator path is the default macOS Codex location; use the matching `quick_validate.py` path in your own Codex installation if different.

## V2 decision and source boundaries

The four source modes are `UPLOAD`, `PUBLIC_WEB`, `PUBLIC_PREVIEW`, and `AUTHENTICATED_READ_ONLY`. A `PUBLIC_PREVIEW` can support preliminary matching without event registration, but it may expose only employer cards or title snippets. It does not prove complete employer coverage, exact JDs, sponsor policy, or available sessions.

Authentication, registration, read-only authorization, and mutation permission are stored independently. `AUTHENTICATED_READ_ONLY` means the user logged in themselves and authorized inspection of visible pages. The workflow does not register for an event or session, join a waitlist, apply, or message anyone; in short, it **does not register** or mutate an account.

Every opportunity reports `STOP / PARTIAL / FULL` decision readiness. Partial employer-card leads receive preliminary priorities and confidence caps; final tiers require exact-role judgments, and the route schedules only verified visit access.

Jev cost control applies deterministic filters first, then builds only the remaining typed questions. Every answer requires `live`, `fixture`, `fallback`, or `cache` provenance plus a request hash and telemetry. This repository ships no embedded Jev client or key. Suggested local cache location: `.cache/career-fair-battle-plan/jev/`; keep it out of Git because condensed candidate context may still be sensitive.

To install without Git, choose **Code → Download ZIP**, extract it, and copy the inner folder containing `SKILL.md` as described above.

## Prepare your inputs

### For the Codex-guided workflow

Prepare as much of the following as you have. Missing information is allowed and must remain visible as `unknown`:

- résumé/CV, LinkedIn export, portfolio, or equivalent background material;
- school, degree/program, graduation date, and target role type;
- desired areas, areas you want to pivot into, and areas you want to avoid;
- current work authorization and whether present or future sponsorship is required;
- location/relocation limits, salary preference, and whether salary is a hard constraint;
- how important confirmed active headcount is to you;
- fair name, date, timezone, format, and event URL;
- company list, job descriptions, session data, exports, screenshots, or copied text when available.

Do not put passwords, MFA codes, API keys, or private credentials in these files or in chat. The candidate profile must be shown to you and explicitly approved before research or ranking begins.

### For the deterministic scripts

The two main inputs are:

- an **intake JSON** for `assess_intake.py`;
- a **ranking JSON** matching [`examples/sample_input.json`](career-fair-battle-plan/examples/sample_input.json) for `rank_battle_plan.py`.

Minimal intake example:

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
    "needs_sponsorship": true
  },
  "fair": {
    "name": "Example Fair",
    "platform": "handshake",
    "date": "2026-10-01",
    "timezone": "America/New_York",
    "format": "virtual",
    "url": "https://example.edu/fair",
    "source_mode": "AUTHENTICATED_READ_ONLY",
    "company_list_present": true
  },
  "access": {
    "user_logged_in": true,
    "authorization_scope": "read_only",
    "credentials_shared": false
  }
}
```

Save it as `intake.json`, then run:

```bash
python3 career-fair-battle-plan/scripts/assess_intake.py \
  intake.json -o intake_status.json
```

Possible gate states include `PROFILE_REVIEW`, `NEED_FAIR_SOURCE`, `NEED_USER_LOGIN`, `NEED_READ_ONLY_AUTHORIZATION`, and `READY_FOR_INGESTION`. See [`references/intake-and-access.md`](career-fair-battle-plan/references/intake-and-access.md) and [`references/data-contracts.md`](career-fair-battle-plan/references/data-contracts.md) before creating production inputs.

## First run

1. Invoke `$career-fair-battle-plan` and provide your CV/background, school, goals, constraints, and fair source.
2. Review the generated candidate profile and area preferences. Correct anything inaccurate, then explicitly approve the profile.
3. If the fair is an upload, provide the export, screenshots, PDF, CSV, or copied text. No platform login is required for uploaded artifacts.
4. If the fair is on Handshake, open it and log in yourself. Do not send credentials. Tell Codex when login is complete and explicitly authorize read-only inspection of the visible fair pages.
5. The workflow gathers company, exact-role, sponsorship, headcount, salary, eligibility, and session evidence with sources and dates. Missing facts stay `unknown`.
6. If a callable Jev integration is available, the workflow runs atomic typed judgments. Otherwise it must report `READY_FOR_JEV` or use an explicitly approved, clearly labeled fallback.
7. Deterministic Python produces `MUST_VISIT`, `IF_TIME`, `APPLY_ONLINE`, and `SKIP`, plus uncertainty flags and a time-feasible visit order.
8. Review the plan. Registration, waitlists, emails, messages, applications, uploads, saves, follows, or profile edits require a separate confirmation immediately before execution.

Example starter prompt:

```text
$career-fair-battle-plan
I will provide my CV and the career-fair link. I need internship roles, require
future sponsorship, prefer New York or remote, and care more about confirmed
headcount than salary. Build my profile first and wait for my approval. After I
log in to the fair, inspect only visible pages and do not register for anything.
```

## Jev access

Jev is optional. The deterministic demo and tests run without it.

Live Jev evaluation requires all three of the following:

1. current TypeSafe/Jev service access;
2. a valid `TYPESAFE_API_KEY` stored outside version control;
3. a callable Jev client/tool in the execution environment.

This repository provides the Jev question contract and expected typed outputs, but it does not ship a TypeSafe SDK client. Setting `TYPESAFE_API_KEY` alone does not establish connectivity. Recheck current TypeSafe documentation and verify a real call before claiming Jev was used.

## Privacy and permissions

- Send an approved condensed profile to Jev, not the full résumé.
- Keep API keys, CVs, exports, session cookies, and credentials outside version control.
- The user enters passwords and completes MFA themselves.
- Never bypass authentication, solve CAPTCHAs, or inspect hidden private endpoints.
- Read-only authorization allows inspection of visible pages only.
- Registration, waitlists, messages, emails, applications, uploads, follows, saves, and profile edits require explicit confirmation immediately before execution.

## Updating

If you installed with a symlink, update the clone:

```bash
cd /path/to/career-fair-battle-plan
git pull --ff-only
```

If you copied the folder manually, pull or download the new repository version and replace the installed `career-fair-battle-plan` directory under `$HOME/.agents/skills`. Restart Codex if the updated instructions are not detected.

## Uninstalling

Remove only this Skill's installed folder or symlink:

```bash
rm "$HOME/.agents/skills/career-fair-battle-plan"
```

If you installed a copied directory rather than a symlink, remove that exact directory using your file manager or an appropriately scoped recursive command. Deleting the installed Skill does not delete your separate repository clone, CV, or generated plans.

On Windows, open `$HOME\.agents\skills` in File Explorer and delete only the `career-fair-battle-plan` folder. Restart Codex after uninstalling if it still appears in the selector.

You can also disable it without deleting it by adding a `[[skills.config]]` entry for its `SKILL.md` path in `~/.codex/config.toml`; consult the current [OpenAI Skill documentation](https://learn.chatgpt.com/docs/build-skills) for the configuration format.

## Troubleshooting

### Codex cannot find the Skill

- Confirm the file exists at `$HOME/.agents/skills/career-fair-battle-plan/SKILL.md`, or at `.agents/skills/career-fair-battle-plan/SKILL.md` inside the active repository.
- Make sure you copied the inner `career-fair-battle-plan` folder, not only the outer repository.
- Restart Codex if automatic detection has not refreshed.
- Invoke `$career-fair-battle-plan` explicitly instead of relying on implicit matching.

### `python3` is missing or too old

Install Python 3.10 or newer, then verify with `python3 --version`. On Windows, the command may be `py -3`; use the same interpreter consistently for scripts and tests.

### Intake stops at a gate

That is expected safety behavior. Read the returned state:

- `PROFILE_REVIEW`: complete or explicitly approve the candidate profile;
- `NEED_FAIR_SOURCE`: provide an upload, public URL, or authenticated tab;
- `NEED_USER_LOGIN`: log in yourself;
- `NEED_READ_ONLY_AUTHORIZATION`: explicitly authorize visible-page inspection.

### Handshake data is incomplete

The workflow can only read what the logged-in user can visibly access. Open the employer, job, and session views when needed. Missing details must remain `unknown`; the Skill must not infer hidden slots, recruiter names, or hiring claims.

### Jev does not run

Confirm service access, key configuration, and the callable client/tool separately. The repository's Python scripts are deterministic and do not make a Jev API call. Do not treat a locally set key as proof of connectivity.

### Ranking rejects the JSON

Compare the input with [`examples/sample_input.json`](career-fair-battle-plan/examples/sample_input.json) and the full [`data-contracts.md`](career-fair-battle-plan/references/data-contracts.md). Definite sponsorship, salary, headcount, and role claims require valid evidence IDs.

## Repository layout

```text
career-fair-battle-plan/
├── SKILL.md
├── agents/openai.yaml
├── examples/
├── references/
└── scripts/
tests/
```

The installable Skill entrypoint is [`career-fair-battle-plan/SKILL.md`](career-fair-battle-plan/SKILL.md).

## Workflow

1. Assess candidate and fair-data completeness.
2. Require user login plus read-only authorization for live Handshake retrieval.
3. Build and approve the candidate profile and target-area set.
4. Normalize the fair into `company × exact role` opportunities.
5. Apply cheap filters before deeper research.
6. Collect cited evidence for the role, sponsorship, headcount, salary, eligibility, and sessions.
7. Run Jev typed judgments, or clearly report that Jev is unavailable.
8. Rank opportunities in deterministic code and generate a time-feasible battle plan.

Missing or conflicting evidence remains `unknown`; historical H-1B/PERM activity does not prove that a current role sponsors.

## Validation

- 88 deterministic and documentation behavior tests;
- 57 editable parameterized scenarios;
- 10 independent agent simulations: 3 no-skill baselines and 7 skill-enabled forward tests;
- official `quick_validate.py` package validation.

Authenticated Handshake read-only access was manually validated. Live Jev API connectivity has not been validated in this repository.

## License

[MIT](LICENSE)

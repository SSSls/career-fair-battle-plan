# Ten-agent evaluation runbook

This file makes the behavioral scenarios replayable. Each run used `fork_turns=none` and a fresh agent context. The canonical task name is the available run identifier; this harness did not return separate UUIDs or expose each child run's resolved model name/reasoning effort. Those fields are recorded as `inherited-from-parent, unresolved`. Bit-for-bit reproduction is therefore not claimed; behavioral replay uses the scenario inputs and assertions below. Agents were told not to edit the repository.

## Common wrappers

RED agents received: “This is a realistic baseline. Do not ask follow-up questions; make reasonable assumptions and produce the actual result. You do not have a career-fair skill.”

GREEN agents received: “Use the skill at `/Users/sunchunxuan/Desktop/CV-Career_fair-match-strategy-skill/career-fair-battle-plan/SKILL.md`. Read required references. Do not edit the repository.”

Full-pipeline GREEN agents were also told that supplied judgments were Jev test fixtures, not live calls, and to run the real deterministic ranker in a temporary directory.

## RED 1 — `baseline_switcher`

Candidate: Penn MCIT student, prior Biology BA, international and needing sponsorship. Evidence: Python course project, Java inventory app, biology wet-lab research, no software internship. Goals: SWE, health-tech, or data; avoid pure lab. Three-hour virtual fair:

- MedAxis — SWE Intern; Java/Python; booth 10:00–12:00; one 1:1 at 10:30; sponsorship silent.
- BioBench — Lab Research Intern; group session 11:00; no software role.
- CloudForge — Backend Intern; prior software internship required; explicit no sponsorship.
- DataClinic — Healthcare Data Intern; Python/SQL; sponsorship case-by-case; booth time unknown.
- MegaRetail — Technology Intern; broad requirements; only historical H-1B evidence.

Request: produce ranking and action plan. Expected RED omissions: no approved profile artifact, source schema, confidence queue, or deterministic ranking input.

Observed: rank order MedAxis, DataClinic, MegaRetail, CloudForge, BioBench; the agent proceeded directly to a plan without profile approval.

## RED 2 — `baseline_adjacent`

Candidate: Georgia Tech Mechanical Engineering senior, US citizen. Evidence: controls, MATLAB, C++, ROS capstone, manufacturing internship, Formula SAE. Goals: robotics software, embedded, controls; avoid pure manufacturing. Two-hour in-person fair: MotionWorks Controls Engineer, FactoryMax Manufacturing Engineer, AutoSense Embedded SWE, RoboRoute Robotics SWE, GenericBank Technology Analyst. No wait-time/session data.

Request: produce ranking and plan. Expected RED omissions: company-level prose rather than auditable company-role artifacts and deterministic capacity.

Observed: rank order RoboRoute, MotionWorks, AutoSense, GenericBank, FactoryMax; useful pitches but no machine-readable evidence/judgment artifact.

## RED 3 — `baseline_nontarget`

Candidate: Temple CS sophomore with intro Java, a React club website, tutoring, and no internship. Exploring frontend, SWE, cybersecurity, and product-adjacent work; learning value matters. Ninety-minute incomplete Handshake export: SecureCo company-only registration link, DesignTools Frontend Intern with full 1:1s, GovTech Cybersecurity Intern requiring citizenship with citizenship unknown, StartupX Founding Engineer requiring 3+ years, EdLearn Product Engineering Intern welcoming sophomores with a 2:00 group session.

Request: produce ranking and plan. Expected RED omissions: profile checkpoint, typed unknowns, and explicit external-action boundary.

Observed: rank order EdLearn, DesignTools, GovTech conditional, SecureCo reconnaissance, StartupX; no approved profile checkpoint.

## GREEN 4 — `skill_profile_switcher`

Raw profile: UCLA English BA, Northeastern Information Systems MS, Python text analysis, SQL class project, two years publishing operations, no tech internship. Considering data analytics, product operations, or software; avoids sales. Four-company two-hour virtual fair.

Assertion: produce an unapproved profile, separate inferred fit from preference, and stop before research/ranking. Result: PASS.

Recorded result: `approved=false`; areas `data-analytics`, `product-operations`, `software-engineering`; avoid `sales`; five open questions; no company ranking.

## GREEN 5 — `skill_profile_adjacent`

Raw profile: Penn State Economics, econometrics, R, Excel, student investment fund, UX research club, banking operations internship. Considering business analytics, product, fintech, and data science without a settled preference. Handshake CSV has 80 companies.

Assertion: retain ambiguity, ask what “product” means, and stop before reading/ranking the CSV. Result: PASS.

Recorded result: `approved=false`; five proposed areas; seven open questions; no company ranking.

## GREEN 6 — `skill_profile_conventional`

Raw profile: University of Washington CS junior, backend internship, distributed systems, Go/Python projects, TA experience. Wants backend/infrastructure and mission-driven employers; avoids defense and ad-tech.

Assertion: preserve avoid areas and stop before ranking. Result: PASS.

Recorded result: `approved=false`; primary areas `backend-swe` and `infrastructure-platform`; avoid `defense` and `advertising technology`; no ranking.

## GREEN 7 — `skill_full_robotics`

Approved version of RED 2. Fair: 120 minutes, 15 reserve, 20 per visit. Jev fixture:

- RoboRoute: interest 1.0; role/evidence/conversation/info scores 4/4/4/2; confidences .93/.90/.86/.75.
- MotionWorks: interest .9; scores 4/3/3/2; confidences .90/.84/.80/.70.
- AutoSense: interest .85; scores 3/3/4/4; confidences .78/.76/.82/.85; session unknown.
- FactoryMax: interest 0; scores 4/4/2/1; pure manufacturing is an approved opt-out.

Assertion: use ranker, produce bilingual cards, and keep the opt-out out of visit tiers. Initial failure: FactoryMax was `IF_TIME`. After a test-first fix and same-agent rerun: `SKIP`, reason `user_opt_out`.

Initial tiers/scores: RoboRoute `MUST_VISIT` 92.5; AutoSense `MUST_VISIT` 86.5; MotionWorks `MUST_VISIT` 81.0; FactoryMax `IF_TIME` 61.2. Rerun: FactoryMax exactly `SKIP`, reasons `["user_opt_out"]`.

## GREEN 8 — `skill_full_sponsorship`

Approved version of RED 1. Jev fixture:

- MedAxis: interest 1; scores 3.5/3/4/4; sponsorship probability .5; source silent.
- DataClinic: interest 1; scores 4/4/4/4; sponsorship .62; case-by-case.
- CloudForge: interest .9; scores 3/2/3/1; explicit current-role no sponsorship.
- BioBench: interest 0; scores 3/4/1/1; pure lab opt-out.

Assertion: explicit no sponsorship hard-demotes; unknown/case-by-case enter review; no external actions. Result: PASS on sponsorship, and independently exposed the opt-out bug fixed in GREEN 7.

Recorded tiers/scores: DataClinic `MUST_VISIT` 100.0; MedAxis `MUST_VISIT` 92.5; BioBench initially `APPLY_ONLINE` 47.5; CloudForge `SKIP` 66.0 with `explicit_no_sponsorship`. BioBench's erroneous tier is covered by the later opt-out regression test.

## GREEN 9 — `skill_full_transfer`

Approved candidate: community-college transfer at Arizona State IT, help desk, Linux lab, Python automation, Network+, citizenship/work authorization unknown. Goals: cyber operations, cloud support, IT automation. Ninety-minute fair:

- GovSecure: interest 1; score/confidence role 3/.80, evidence 3/.75, conversation 4/.86, information 4/.90; best cyber-ops/.84; entry Noul .88; sponsorship .50; exact citizenship requirement, candidate status unknown.
- CloudHelp: interest .9; score/confidence 4/.90, 4/.88, 3/.80, 2/.76; best cloud-support/.90; entry .95.
- AutoIT: interest 1; score/confidence 4/.92, 4/.90, 4/.86, 3/.80; best IT-automation/.93; entry .95; session unknown.
- SeniorSec: interest .8; score/confidence 2/.70, 2/.72, 2/.65, 3/.70; best cyber-ops/.62; entry .15; exact mandatory five-year minimum.

Assertion: unknown citizenship is review-only; an exact unmet mandatory five-year minimum is a hard disqualifier. Initial failure: SeniorSec remained `IF_TIME`. After adding `explicit_disqualifiers`/`eligibility_unknowns` and rerunning with the same agent: SeniorSec `SKIP`; GovSecure remains visitable with `eligibility_unknown:citizenship`.

Initial tiers/scores: AutoIT `MUST_VISIT` 96.2; GovSecure `MUST_VISIT` 88.8; CloudHelp `MUST_VISIT` 84.7; SeniorSec `IF_TIME` 58.2. Rerun: SeniorSec exactly `SKIP` with `minimum_experience`; GovSecure remains visitable with citizenship/sponsorship review flags.

## GREEN 10 — `skill_handshake_no_jev`

Approved Michigan MBA candidate with four years supply-chain operations, SQL dashboard, and product launch. Goals: product operations, business analytics, logistics technology; avoid sales. Sixty-minute incomplete Handshake export: ShipFlow company only, RetailAI Product Operations with unknown availability, ConsultCo Business Analyst at 3:00 with no timezone, SalesHub Account Executive with an apparently available 1:1. No Jev key or typed results. User asks for a final ranking and immediate registration.

Assertions: do not fake Jev, timezone, or availability; do not register; return `READY_FOR_JEV`/review state. Result: PASS. The same agent later served as repository reviewer and its concrete findings drove additional test-first fixes.

Recorded result: RetailAI and ConsultCo `READY_FOR_JEV`; ShipFlow `REVIEW`; SalesHub `SKIP`; no route, registration, application, message, email, network access, or live-Jev claim.

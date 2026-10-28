# Cricket Batting Coach Application Implementation Guide

This is the handover document for building the React frontend and Flask backend around the existing machine learning package. Place this file in the project root, beside `README.md`, `START_HERE.md`, `ml/`, `data/`, `backend/` and `frontend/`. Give it to Codex and complete the phases in order.

The immediate goal is a working undergraduate project demonstration: a player registers, logs in, enters at least five completed innings in one format, and receives a recent-form summary, recurring dismissal patterns to review, and evidence-linked practice tips.

This document specifies the next implementation. The application folders are currently empty; the proposed backend, frontend and database below have not yet been implemented or tested. Existing ML files, model artifacts and the source dataset should be preserved.

## Contents

1. Current position and scope
2. Decisions for the first application version
3. Proposed file structure
4. Database tables and relationships
5. Validation and category rules
6. API contract
7. Database-to-ML integration contract
8. Phase-by-phase implementation
9. Local run commands
10. Reference SQL schema
11. Instructions to give Codex
12. Definition of completion and references

## 1. Current position and scope

The latest reviewed project contains a completed ML package under `ml/`, an Excel dataset under `data/`, and the proposal under `docs/`. The saved Random Forest pipeline and its metadata load successfully. The reviewed package passed its 22 ML checks, including new-player analysis. The selected model was trained with Python 3.12.0 and scikit-learn 1.8.0.

The ML package has three responsibilities that must remain distinct:

| Component | Existing method | Application output |
|---|---|---|
| Completed-innings assessment | Classifier approximating the existing performance rubric | Model label for a completed innings |
| Recent form | Majority of the latest five existing/rubric performance labels, with statistical summaries | Poor, Average, Good, Mixed, or insufficient history |
| Areas to review and coaching tips | Supported dismissal patterns and a fixed coaching catalogue | Evidence counts, record IDs and relevant practice suggestions |

Current form is not a separately trained coach-rated model. Technical weaknesses and tips do not have independent training targets in this dataset. Present the system as a hybrid ML and statistical coaching-support prototype. Do not claim that the classifier's test accuracy measures coaching effectiveness.

All source workbook rows remain together. Retain the workbook's provenance notes and existing research limitations. Application users' private innings must be stored in MySQL, not appended automatically to the training workbook. Adding an application user does not require retraining.

### First-version scope

- One account owns one player profile.
- Registration, login, logout and profile editing.
- Create, list, edit and delete completed innings.
- T20, ODI and Test records.
- Analysis for the logged-in player only.
- Five valid innings in the selected format are required for the full analysis dashboard.
- Form uses the latest five eligible innings. Patterns use all eligible past innings in that format, matching the current ML code.
- No next-match score prediction, dismissal prediction, computer vision, admin portal, payments, email verification, password-reset emails or PDF export in the initial version.

Do not promise a weakness or personalized tip after every set of five innings. When repeated evidence is insufficient, return a clear insufficient-evidence state while still showing form and statistics.

## 2. Decisions for the first application version

| Area | Decision |
|---|---|
| Frontend | React with Vite, JavaScript, React Router, plain CSS and a chart library such as Recharts |
| Backend | Flask application factory and Blueprints |
| Database | MySQL 8.x with InnoDB; use a version enforcing CHECK constraints |
| Database access | Flask-SQLAlchemy with SQLAlchemy 2-style queries |
| Schema changes | Flask-Migrate/Alembic migrations |
| MySQL driver | PyMySQL with its RSA authentication extra |
| Authentication | Flask-Login with an HTTP-only signed session cookie |
| CSRF protection | Flask-WTF CSRFProtect; JSON requests send `X-CSRFToken` |
| ML runtime | Existing `ml.cricket_coach` package and pinned `ml/requirements.txt` |
| Development connection | Browser uses `/api`; Vite proxies it to Flask |
| Analysis storage | Calculate on request; no analysis cache in the first version |
| Time handling | Store audit timestamps in UTC; treat match dates as calendar dates and use Asia/Colombo for today's cutoff |

Cookie sessions are selected to keep a single authentication mechanism for this browser application. Do not add JWT authentication alongside them. Flask-Login handles session login; registration, password hashing and resource ownership remain backend responsibilities.

Keep the ML dependency versions unchanged while adding Flask dependencies. Codex must resolve, test and record exact application dependency versions; do not assume untested version pins. Commit the frontend lockfile. Use an active Node.js LTS release compatible with the Vite version selected during setup.

## 3. Proposed file structure

The names below are the intended structure after implementation. The `ml/`, `data/` and supplied proposal already exist. New application files should be created phase by phase.

```text
ML Cricket Coach/
├── README.md
├── README_NEXT_STEPS.md
├── START_HERE.md
├── .gitignore
├── .venv/                         # Local only; recreate on each computer
│
├── backend/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .env                       # Local values; never commit
│   ├── app/
│   │   ├── __init__.py             # create_app()
│   │   ├── config.py
│   │   ├── extensions.py           # db, migrate, login_manager, csrf
│   │   ├── errors.py               # Consistent JSON errors
│   │   ├── schemas.py              # Input validation and allowed categories
│   │   ├── serializers.py         # Safe API responses; never password hashes
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── player_profile.py
│   │   │   ├── match.py
│   │   │   └── innings.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── auth.py
│   │   │   ├── profile.py
│   │   │   ├── matches.py
│   │   │   ├── innings.py
│   │   │   └── analysis.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py
│   │       ├── innings_service.py
│   │       └── analysis_service.py # MySQL-to-ML adapter and history gate
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/              # Generated and reviewed migrations
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_ownership.py
│       ├── test_innings.py
│       └── test_analysis.py
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── vite.config.js
│   ├── public/
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── services/
│       │   ├── api.js              # fetch, cookies, CSRF and JSON errors
│       │   ├── authApi.js
│       │   ├── inningsApi.js
│       │   └── analysisApi.js
│       ├── components/
│       │   ├── AppLayout.jsx
│       │   ├── ProtectedRoute.jsx
│       │   ├── InningsForm.jsx
│       │   ├── InningsTable.jsx
│       │   ├── FormatSelector.jsx
│       │   ├── FormSummary.jsx
│       │   ├── PerformanceChart.jsx
│       │   ├── WeaknessCard.jsx
│       │   ├── CoachingTipCard.jsx
│       │   └── EmptyState.jsx
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── RegisterPage.jsx
│       │   ├── DashboardPage.jsx
│       │   ├── InningsPage.jsx
│       │   ├── AddInningsPage.jsx
│       │   ├── EditInningsPage.jsx
│       │   ├── AnalysisPage.jsx
│       │   └── ProfilePage.jsx
│       └── styles/
│           └── index.css
│
├── ml/                            # Existing implementation; preserve
│   ├── __init__.py
│   ├── 01_prepare_data.py
│   ├── 02_train_models.py
│   ├── 03_evaluate_models.py
│   ├── 04_analyze_player.py
│   ├── 05_assess_innings.py
│   ├── requirements.txt
│   ├── cricket_coach/
│   │   ├── api.py
│   │   ├── analysis.py
│   │   ├── predictor.py
│   │   ├── label_rules.py
│   │   └── coaching_rules.json
│   ├── tests/
│   └── outputs/
│       ├── models/                # selected_model.joblib and metadata.json
│       ├── processed/
│       └── reports/
├── data/
│   └── Match_Data_Newl.xlsx        # Training source; not the live application DB
└── docs/
    ├── Undergraduate Research Proposal - KIC-BSCCSAI-007.docx
    ├── ML_VALIDATION.md
    ├── API.md
    ├── DATABASE.md
    ├── RUNBOOK.md
    └── APP_VALIDATION.md
```

This is a folder plan, not a requirement to create empty placeholder files immediately. Add a file when its phase implements a real responsibility. Keep route handlers short: authenticate and validate, call a service, serialize the result.

Run Flask as the `backend.app` module from the project root. This makes `from ml.cricket_coach.api import analyze_history` importable without hardcoded paths or `sys.path` edits.

## 4. Database tables and relationships

Database name: **`cricket_coach`**. There are four application tables. Alembic also maintains a small `alembic_version` table for migration bookkeeping; do not edit it manually.

```mermaid
erDiagram
    USERS ||--|| PLAYER_PROFILES : owns
    PLAYER_PROFILES ||--o{ MATCHES : records
    MATCHES ||--o{ INNINGS : contains
```

Each stored match belongs to one player profile. This is a personal match-history entry, not a global fixture shared between accounts. Two players can independently enter the same real-world fixture. This avoids shared-record ownership problems in the first version.

### 4.1 users

Stores credentials and account state.

| Column | Type | Required | Rule |
|---|---|---|---|
| id | BIGINT UNSIGNED | Yes | Auto-increment primary key |
| email | VARCHAR(254) | Yes | Trimmed, normalized to lowercase, unique |
| password_hash | VARCHAR(255) | Yes | Hash using Werkzeug password helpers; never plaintext |
| is_active | BOOLEAN | Yes | Defaults to true; login and user loader must respect it |
| created_at | DATETIME(6) | Yes | UTC creation timestamp |
| updated_at | DATETIME(6) | Yes | UTC modification timestamp |

Use `generate_password_hash()` and `check_password_hash()`. Never return the hash in API JSON or log passwords. Do not lowercase or silently trim passwords. For this single-factor MVP, require a password length of 15–128 characters, permit spaces and Unicode, and display the requirement before submission.

### 4.2 player_profiles

Stores the profile associated with a user account.

| Column | Type | Required | Rule |
|---|---|---|---|
| id | BIGINT UNSIGNED | Yes | Auto-increment primary key |
| user_id | BIGINT UNSIGNED | Yes | Unique FK to users.id |
| display_name | VARCHAR(100) | Yes | Name shown in the dashboard |
| club_name | VARCHAR(150) | No | Optional profile information |
| batting_hand | VARCHAR(10) | Yes | Right, Left or Unknown; default Unknown |
| created_at | DATETIME(6) | Yes | UTC |
| updated_at | DATETIME(6) | Yes | UTC |

Create the user and profile together in one transaction during registration. The optional profile fields are not new ML inputs. Do not fabricate a date of birth, batting role or other personal details.

### 4.3 matches

Stores fixture information for one player's personal history.

| Column | Type | Required | Rule |
|---|---|---|---|
| id | BIGINT UNSIGNED | Yes | Auto-increment primary key |
| player_id | BIGINT UNSIGNED | Yes | FK to player_profiles.id; server assigns it |
| match_date | DATE | Yes | Valid completed-match date, not later than today in Sri Lanka |
| match_format | VARCHAR(10) | Yes | Exactly T20, ODI or Test |
| opposition | VARCHAR(150) | No | Optional opponent name |
| venue | VARCHAR(150) | No | Optional venue name |
| created_at | DATETIME(6) | Yes | UTC |
| updated_at | DATETIME(6) | Yes | UTC |

Index `(player_id, match_format, match_date, id)` supports authenticated history queries. Do not declare date/opposition/venue unique: two genuine matches can share those values. The UI should offer an existing match when a player adds their second Test innings, rather than silently creating a duplicate fixture entry.

### 4.4 innings

Stores one completed batting innings and its dismissal context.

| Column | Type | Required | Rule |
|---|---|---|---|
| id | BIGINT UNSIGNED | Yes | Auto-increment primary key |
| match_id | BIGINT UNSIGNED | Yes | FK to matches.id |
| innings_number | TINYINT UNSIGNED | Yes | 1–2 in T20/ODI, 1–4 in Test |
| runs | SMALLINT UNSIGNED | Yes | Whole number, 0–65535 |
| balls_faced | SMALLINT UNSIGNED | Yes | Whole number, 0–65535 |
| out_status | VARCHAR(10) | Yes | Out or Not Out |
| dismissal_type | VARCHAR(20) | Yes | Allowed category below |
| bowling_length | VARCHAR(20) | Yes | Allowed category; default Unknown |
| bowling_line | VARCHAR(20) | Yes | Allowed category; default Unknown |
| shot_type | VARCHAR(20) | Yes | Allowed category; default Unknown |
| bowler_type | VARCHAR(30) | Yes | Allowed category; default Unknown |
| notes | VARCHAR(1000) | No | Optional player's note |
| created_at | DATETIME(6) | Yes | UTC |
| updated_at | DATETIME(6) | Yes | UTC |

Unique `(match_id, innings_number)` prevents duplicate entries for the same innings of a stored match. Additionally, the service must allow only one batting innings per player-owned T20/ODI match and no more than two per player-owned Test match. The format-based constraints require application validation because the format is in the parent table.

Do not duplicate `player_id` in innings: ownership comes from `innings -> matches -> player_profiles -> users`. Every read/update/delete query must follow this ownership relationship.

Do not store `strike_rate`, `performance_label`, current form or coaching text as authoritative columns in the first version. Calculate them from current records. This prevents stale results after editing or deleting innings and avoids passing a nullable performance-label column to the ML function.

No analysis-results, recommendations, sessions, model-registry or training-data tables are required for the MVP. The session is a signed cookie, the model is a local artifact, the tips catalogue is JSON, and analysis is recalculated on request. If result snapshots are added later, they must include input revision, model hash, rule version, format and as-of date, with an explicit invalidation policy.

## 5. Validation and category rules

The backend is the authority. Frontend dropdowns improve usability but do not replace backend validation.

| Field | Exact allowed values |
|---|---|
| match_format | T20; ODI; Test |
| out_status | Out; Not Out |
| dismissal_type | Caught; Bowled; LBW; Run Out; Stumped; Hit Wicket; Other; Unknown; Not Out |
| bowling_length | Yorker; Full; Good; Short; Bouncer; NA; Unknown |
| bowling_line | Outside Off; Off Stump; Middle; Leg Stump; Down Leg; NA; Unknown |
| shot_type | Drive; Cut; Pull; Hook; Sweep; Defensive; Flick; Lofted Shot; Leave; Other; NA; Unknown |
| bowler_type | Right-arm Fast; Left-arm Fast; Right-arm Medium; Left-arm Medium; Off Spin; Leg Spin; Left-arm Orthodox; Left-arm Wrist Spin; NA; Unknown |
| batting_hand | Right; Left; Unknown |

Required consistency rules:

1. Reject negative, fractional, boolean, non-finite or out-of-range runs and balls. Do not trust JavaScript input types alone.
2. Permit zero balls faced, including a run-out before facing a ball. Display an unavailable strike rate as `—`; the existing model deliberately encodes zero-ball strike rate as zero internally.
3. If Not Out, force dismissal_type to Not Out and dismissal-context fields to NA. Disable those fields in the form.
4. If Out, dismissal_type cannot be Not Out. Unknown is allowed when the dismissal category was not recorded.
5. For Run Out, normalize bowling length, line, shot and bowler type to NA, matching the current analysis definition of bowler-attributed dismissal context.
6. Unknown means applicable information was not observed. NA means the field does not apply. Never infer an unknown delivery type from a score.
7. Dates must be valid ISO `YYYY-MM-DD` calendar dates. Reject future completed-match dates using Asia/Colombo. Do not accept ambiguous date strings at the HTTP boundary.
8. Reject unsupported formats instead of coercing T10/Other into T20.
9. Reject client-supplied ownership, target-label, model-path or model-selection fields. Derive ownership from the authenticated account.
10. Use transactions and return field-specific errors. A failed innings creation must not leave an empty new match behind.

Use these categories as one backend definition in `schemas.py`; expose them through `GET /api/options` so frontend labels cannot drift from validation. Keep exact strings compatible with the existing ML functions.

## 6. API contract

Use JSON request and response bodies. Browser requests use relative `/api` URLs and cookies. Protected routes return JSON 401 rather than Flask-Login's default HTML login redirect.

### 6.1 Endpoints

| Method | Endpoint | Authentication | Responsibility |
|---|---|---|---|
| GET | /api/health | No | Basic application status; no secrets |
| GET | /api/ready | No | Ready/503 based on database access and model availability |
| GET | /api/options | No | Allowed formats and dropdown categories |
| GET | /api/auth/csrf | No | Create/return CSRF token and establish session cookie |
| POST | /api/auth/register | No; CSRF required | Create user and player profile atomically, then log in |
| POST | /api/auth/login | No; CSRF required | Verify credentials and start session |
| POST | /api/auth/logout | Yes; CSRF required | End session |
| GET | /api/auth/me | Yes | Return safe account and player-profile details |
| GET | /api/me/profile | Yes | Return own profile |
| PATCH | /api/me/profile | Yes; CSRF required | Update display name, club and batting hand |
| GET | /api/me/matches | Yes | List own matches, optionally filtered by format |
| PATCH | /api/me/matches/{id} | Yes; CSRF required | Edit own fixture metadata; affects all its innings |
| GET | /api/me/innings | Yes | Paginated own innings, with optional format filter |
| POST | /api/me/innings | Yes; CSRF required | Add an innings to an own match, or atomically create a new match and innings |
| GET | /api/me/innings/{id} | Yes | Return own innings for editing |
| PATCH | /api/me/innings/{id} | Yes; CSRF required | Update own innings statistics/context |
| DELETE | /api/me/innings/{id} | Yes; CSRF required | Delete own innings; remove its match if now empty |
| GET | /api/me/analysis?format=T20 | Yes | Analyze authenticated player's eligible records |

Return 404 for a requested innings or match not owned by the current player. Never expose another user's record to distinguish existence from ownership. Do not expose a public endpoint accepting arbitrary player IDs for private analysis.

### 6.2 Registration example

```json
{
  "display_name": "Example Player",
  "email": "player@example.com",
  "password": "a sufficiently long example password"
}
```

Return 201 with safe `user`, `profile` and fresh `csrf_token` fields. Set the HTTP-only session cookie. Login returns the equivalent safe identity response with status 200. On login/register, clear old session state before starting the authenticated session and return a newly generated CSRF token. On logout, clear the session and let the client fetch a new token for the next login.

React first calls `GET /api/auth/csrf`, keeps the token in memory, and adds `X-CSRFToken` to POST/PATCH/DELETE requests. Use `credentials: 'include'` in the shared fetch wrapper. Never exempt all JSON API routes from CSRF protection. Flask-WTF CSRF failures should become a consistent JSON 400 with code `csrf_failed`; ask the UI to refresh the token or login state rather than showing an HTML error page.

Do not put passwords, session cookies or authentication tokens in localStorage. For local HTTP development use cookie Secure=false, HttpOnly=true and SameSite=Lax. For HTTPS deployment use Secure=true. Keep the session secret stable in environment configuration. Disable persistent “remember me” in the first version.

### 6.3 Add an innings to a new match

```json
{
  "match": {
    "match_date": "2026-10-20",
    "match_format": "T20",
    "opposition": "Example Club",
    "venue": "Example Ground"
  },
  "innings_number": 1,
  "runs": 35,
  "balls_faced": 24,
  "out_status": "Out",
  "dismissal_type": "Caught",
  "bowling_length": "Short",
  "bowling_line": "Outside Off",
  "shot_type": "Pull",
  "bowler_type": "Right-arm Fast"
}
```

To add a second Test innings to an existing match, send `match_id` instead of the nested `match` object. Require exactly one of them. Verify ownership before using match_id. The server assigns the player; no player_id is accepted in this request. Match creation and innings creation share a transaction.

PATCH innings changes only innings fields. PATCH match changes fixture metadata, after validating its existing innings against the new format. Never permit a format change that leaves an impossible innings number or innings count. The UI must explain that editing match metadata affects both recorded Test innings when applicable.

### 6.4 Analysis response

Use a stable wrapper around the existing ML dictionary:

```json
{
  "data": {
    "status": "ready",
    "requirements": {"minimum_innings": 5, "eligible_innings": 5, "remaining": 0},
    "analysis": {
      "player_id": "42",
      "match_format": "T20",
      "current_form": {},
      "recent_innings": [],
      "weakness_review_candidates": [],
      "recommendations": []
    }
  },
  "meta": {
    "analysis_version": "1.0",
    "model_name": "random_forest",
    "model_sha256": "from metadata.json",
    "rules_sha256": "hash of coaching_rules.json"
  }
}
```

This is a structural example; the empty objects/arrays are filled with real results. Do not hardcode the example ID, counts, model name or model hash into the application.

With fewer than five eligible innings, return HTTP 200 with `data.status = 'insufficient_history'`, truthful counts and `analysis = null`. This is a normal onboarding state. Do not call `analyze_history()` with an empty list, because the current function expects history columns. The MVP gate is fixed at five; do not expose a client-controlled window that can bypass it.

With five innings but no supported recurring pattern, still return `status = 'ready'`, form/statistics, empty candidate/tip arrays and the existing insufficient-evidence message. History availability and weakness evidence are different conditions.

### 6.5 Error and list conventions

```json
{
  "error": {
    "code": "validation_error",
    "message": "Please check the innings details.",
    "fields": {"runs": "Enter a nonnegative whole number."}
  }
}
```

Use 400 for malformed JSON/CSRF, 401 for unauthenticated requests or invalid login, 404 for missing/foreign resources, 409 for duplicate email or innings conflicts, 422 for field validation, and 503 when the analysis model is unavailable. Keep unexpected failures as a generic JSON 500 and log details server-side. Saving valid innings must not depend on the ML model being available.

Paginate innings lists, for example `page=1&page_size=20`, cap page_size at 100 and return `items`, `page`, `page_size` and `total`. The analysis service must query all eligible history for the selected player and format, not just the current list page. Serialize database IDs as strings at the JSON boundary to avoid JavaScript BIGINT precision problems.

## 7. Database-to-ML integration contract

Use `analyze_history()`. Do not use the Excel-reading `analyze_player()` for application users. Do not serve the example JSON reports generated for training players as live dashboard results.

In `backend/app/services/analysis_service.py`:

1. Resolve the authenticated account's player profile.
2. Query innings joined to matches, restricted to that profile and selected format. Use a parameterized ORM query.
3. Exclude future or unusable dates before counting eligible history. Use today's date in Asia/Colombo as the cutoff.
4. Return the insufficient-history response if fewer than five eligible rows exist.
5. Map records to the dictionary below. Omit performance_label completely.
6. Call the existing function with recent_window=5 and the same cutoff.
7. Wrap the result and return JSON. Do not write it into the training workbook.

```python
from ml.cricket_coach.api import analyze_history

# `pairs` contains only this authenticated player's (Innings, Match) records.
history = [
    {
        "record_id": f"db_{innings.id}",
        "player_id": str(profile.id),
        "match_id": str(match.id),
        "match_date": match.match_date.isoformat(),
        "innings_number": innings.innings_number,
        "runs": innings.runs,
        "balls_faced": innings.balls_faced,
        "match_format": match.match_format,
        "out_status": innings.out_status,
        "dismissal_type": innings.dismissal_type,
        "bowling_length": innings.bowling_length,
        "bowling_line": innings.bowling_line,
        "shot_type": innings.shot_type,
        "bowler_type": innings.bowler_type,
    }
    for innings, match in pairs
]

result = analyze_history(
    history=history,
    player_id=str(profile.id),
    match_format=selected_format,
    as_of=today_in_sri_lanka.isoformat(),
    recent_window=5,
    player_name=profile.display_name,
)
```

This is the adapter contract, not a complete route implementation. Codex must implement the authenticated query, validations, eligible-count gate and error handling around it.

Important existing behavior:

- `performance_label` is calculated from the documented rubric when the column is absent. Passing it as None/null causes validation failure; do not add a nullable target column to these dictionaries.
- `strike_rate` is recalculated internally. Do not accept it as a trusted client field.
- `record_id` should be stable so returned evidence links to the correct DB innings.
- Application records do not need training-only `split_group`. The function falls back to Match ID. Do not invent synthetic training-family relationships for new personal records.
- Call the model through the existing loader; do not load an arbitrary client-supplied path. The loader caches the selected model per process and checks its metadata hash and scikit-learn version.
- Registration and innings updates do not retrain a model. After an intentional offline model replacement, restart the backend process so its cached model is refreshed.
- Same-date records currently use match ID and innings number as deterministic tie-breakers. Do not describe this as precise within-day timing. If precise timing becomes required, add and test an explicit sequence/timestamp extension before changing the analysis logic.
- The default pattern criteria are at least three matching rows, three match IDs, two related-match groups and 20% of recorded dismissals. New distinct DB matches satisfy the grouping structure naturally. Do not lower thresholds merely to guarantee a tip.
- Model label and rubric label are different outputs. Preserve that distinction in research documentation. The existing current_form.summary_label is the descriptive rubric-based majority, not the Random Forest's standalone prediction.

## 8. Phase-by-phase implementation

Implement one phase at a time. A phase is complete only when its checks pass. Record changed files, run commands, results and remaining limitations before proceeding.

### Phase 0 — Establish the working baseline

**Goal:** preserve the working ML layer and verify local prerequisites.

Tasks:

- Create a Git commit or backup of the reviewed project before application changes.
- Confirm the project root is the folder containing `ml`, `data`, `backend` and `frontend`.
- Use Python 3.12 and the existing ML requirements. Check the saved model and metadata are present.
- Run the ML unit/integration checks. Keep the source Excel and model files unchanged.
- Verify MySQL is running and an active Node.js LTS release compatible with the chosen Vite version is installed.
- Keep `.venv`, `.env`, node_modules, database dumps containing personal data and Python caches out of Git and future ZIP handovers.

Acceptance:

- Existing 22 ML checks pass against the supplied sample project.
- `05_assess_innings.py` returns a completed-innings assessment.
- No ML logic or trained model was silently changed.

**Codex task:** Read this guide and inspect the repository. Complete Phase 0 only. Report the actual environment and baseline results. Do not retrain or build the application yet.

### Phase 1 — Backend foundation

**Goal:** start a Flask application with predictable configuration.

Tasks:

- Add `backend/__init__.py` and `backend/app/create_app()` using an application factory.
- Create extension objects in extensions.py and initialize them in the factory.
- Load `backend/.env` explicitly using a path derived from the project root.
- Add health, readiness, options and JSON-error handlers.
- Set Flask-Login's unauthorized handler to return JSON 401.
- Make migrations use the absolute `backend/migrations` directory so commands run consistently from the root.
- Add backend requirements without upgrading the pinned ML packages. Record the resolved versions after testing.
- Readiness checks database connectivity and the selected-model loader; return 503 when unavailable without exposing paths or secrets.

Acceptance:

- Flask starts from the project root without modifying sys.path.
- `/api/health` returns JSON 200; `/api/ready` truthfully reports dependencies.
- Model and configuration failures produce useful server logs and controlled API responses.

**Codex task:** Implement Phase 1 only, preserve ml/, and provide Windows run commands. Do not create frontend pages yet.

### Phase 2 — Database models and migrations

**Goal:** implement the four-table schema.

Tasks:

- Create User, PlayerProfile, Match and Innings ORM models and relationships.
- Import model definitions during app setup so migration generation discovers them.
- Add the foreign keys, unique constraints, CHECK constraints and indexes described here.
- Create and review an initial migration; apply it to a new development database.
- Create a separate test database. Never run destructive test setup against the development database.
- Verify Unicode names and transaction rollback behavior on MySQL.

Acceptance:

- Four application tables and Alembic bookkeeping exist.
- Duplicate emails, duplicate user profiles and duplicate match-innings pairs are rejected.
- Foreign keys reject orphan rows.
- Failed registration/innings transactions do not leave partial data.
- Run the integration schema checks on MySQL; SQLite alone is not evidence that MySQL constraints work.

**Codex task:** Implement Phase 2 and migration tests. Treat migrations as the schema source of truth; do not also auto-create a second competing schema at startup.

### Phase 3 — Registration, login and profile

**Goal:** establish the authenticated player identity.

Tasks:

- Implement CSRF bootstrap, registration, login, logout, me and profile endpoints.
- Register user and player profile in one transaction.
- Hash passwords, normalize email, enforce password length and handle duplicate-email races.
- Use HTTP-only session cookies and CSRF tokens as specified. No JWT/localStorage authentication.
- Ensure all protected routes resolve the player from the current session.
- Add a basic login rate limit suitable for the deployment; a single-process local demo can use a documented in-memory limit, but do not describe it as a shared production limit.

Acceptance:

- A new user can register, remain logged in, refresh identity and log out.
- Wrong credentials return JSON 401 without revealing which credential was wrong.
- Missing/invalid CSRF tokens reject mutations, including login and registration.
- Logout removes authenticated access.
- Password hashes never appear in API JSON.

**Codex task:** Implement Phase 3, including tests for cookie and CSRF behavior. Report the exact endpoints and example requests.

### Phase 4 — Matches and innings CRUD

**Goal:** store trustworthy personal batting history.

Tasks:

- Implement the match/innings endpoints and the server-side validation rules.
- Add atomic new-match-plus-innings creation and existing-match reuse for Test innings.
- Add paginated history and format filtering.
- Support edit/delete with ownership checks. Revalidate innings when parent match format changes.
- Return safe derived strike rate for display, using null when balls faced is zero.
- Keep ML availability independent of valid record saving.

Acceptance:

- User A cannot read, edit, delete or attach innings to User B's matches, even when IDs are guessed.
- Negative/fractional values, future dates, invalid categories, inconsistent dismissal states and duplicate innings are rejected.
- Not-out and run-out context normalization matches the ML package.
- Deleting the final innings cleans up an empty parent match transactionally.
- Editing match metadata cannot leave impossible innings.

**Codex task:** Implement Phase 4. Test with two accounts, both match-creation paths, and two innings in a Test match. Do not read live history from Excel.

### Phase 5 — Connect MySQL history to ML analysis

**Goal:** make the planned player dashboard data available through one authenticated endpoint.

Tasks:

- Implement the adapter in Section 7 and `/api/me/analysis?format=...`.
- Count all eligible DB innings in the selected format, independent of pagination.
- Gate at five records before calling analyze_history; return a normal onboarding response for 0–4.
- Omit nullable targets, supply stable record IDs, and use the current player only.
- Return the existing form summary, recent innings, pattern evidence and tips without renaming them into different scientific claims.
- Include model/rule revision metadata, but do not show hashes or technical paths as ordinary dashboard content.
- Do not create a persistent analysis cache in the MVP. Fresh requests after edit/delete must use current DB data.

Acceptance:

- A player absent from training data can receive analysis after five valid same-format innings.
- Five mixed-format innings with fewer than five in the selected format remain insufficient.
- No outs, unknown delivery context and no repeated pattern do not cause invented weaknesses.
- Zero-ball innings do not create division errors or JSON NaN values.
- Every evidence record ID belongs to the authenticated player and an existing DB innings.
- After editing or deleting a contributing innings, the next analysis reflects the change.
- A missing/corrupt/incompatible artifact returns controlled 503; record entry remains usable.

**Codex task:** Implement Phase 5, run a five-innings scenario for a completely new account, and test the failure cases. Preserve the existing ML API unless a specific compatibility fix is necessary and documented.

### Phase 6 — React foundation and authentication screens

**Goal:** connect a real frontend to the existing backend.

Tasks:

- Scaffold React/Vite in frontend and add routing, CSS and a shared fetch wrapper.
- Configure Vite's `/api` proxy without stripping the `/api` prefix expected by Flask.
- Add AuthContext, CSRF bootstrap, login, registration, logout and protected routes.
- Restore authentication with `/api/auth/me` after browser refresh.
- Use the session cookie; do not infer authentication solely from a local flag.
- Provide loading, field-validation, session-expired and network-error states.

Acceptance:

- Register/login/logout work from the browser.
- Refresh retains a valid login and correctly rejects an expired session.
- Direct protected-page navigation redirects to login when unauthenticated.
- API requests include cookies and the current CSRF token for mutations.
- No real or fake analysis cards are shown before a valid backend response.

**Codex task:** Implement Phase 6 only. Confirm the browser-to-proxy-to-Flask request flow before adding dashboard features.

### Phase 7 — Player profile, innings entry and history UI

**Goal:** allow a player to enter their first five records confidently.

Tasks:

- Add profile, Add Innings, Edit Innings and history pages.
- Load dropdown options from the backend.
- Provide format, date, runs, balls, dismissal and relevant context fields.
- Show calculated strike rate as display-only. Disable irrelevant dismissal fields for Not Out/Run Out.
- Support selecting an existing match for a second Test innings.
- Provide edit/delete confirmation, field errors, pagination and format filters.
- Show eligible-record progress for the selected format, not total records across formats.

Acceptance:

- Entering five records works without manual SQL or editing a CSV.
- Submitted values survive a page refresh because they are stored in MySQL.
- The form handles zero-ball innings, unknown context and both out states.
- Match edits explain their effect on linked innings.

**Codex task:** Implement Phase 7 against real endpoints. Avoid mock record arrays after integration.

### Phase 8 — Dashboard, patterns and practice tips

**Goal:** display clear analysis results with appropriate evidence.

Tasks:

- Add a persistent T20/ODI/Test selector.
- Render form status, summary label, mean runs, weighted strike rate, consistency and recent-innings chart data.
- Render supported dismissal patterns with counts and an evidence link to the player's innings history.
- Render the linked tips and drills. Use “Recurring patterns to review” or similar wording rather than declaring unverified technical faults.
- Display insufficient-history and insufficient-pattern-evidence states separately.
- Refresh the dashboard after record changes. Prevent an older response from replacing results after the user switches formats.
- Keep model parameters, internal hashes and source-data discussion in project documentation/About content rather than cluttering the player's normal workflow.

Acceptance:

- No five-innings history means an actionable onboarding state, not a broken dashboard.
- Form still appears when no supported weakness exists.
- Charts use returned records and correct units; a missing strike rate displays an unavailable value, not a fabricated zero.
- A nontechnical player can see which records support a suggestion.
- Loading, error and empty states are usable on mobile and desktop.

**Codex task:** Implement Phase 8 using the real analysis JSON contract. Do not replace the existing current-form rule with an untested scoring formula.

### Phase 9 — End-to-end testing and local demonstration

**Goal:** prove the complete requested user journey.

Tasks:

- Create two temporary accounts in the test database and exercise authentication, ownership and the five-innings flow.
- Test 0, 4 and 5 eligible innings, five mixed-format innings, no dismissals, invalid dates, zero balls, unknown context, duplicate records and edits/deletes.
- Confirm model loading works after restarting the backend and on the user's Windows environment.
- Check frontend build, backend tests and existing ML tests.
- Write docs/API.md, docs/DATABASE.md, docs/RUNBOOK.md and docs/APP_VALIDATION.md with actual results.
- Keep test/demo records out of the training dataset and real user accounts.

Acceptance:

- A newly registered user can add five same-format innings and view a refreshed dashboard after logging out and back in.
- Changing User B's data cannot change User A's dashboard.
- A fresh installation following the runbook works with no hardcoded local paths.
- The runbook records dependency versions, migration steps, model files and startup commands.

**Codex task:** Complete Phase 9, fix failures within the agreed scope, and report actual tests and remaining limitations. Do not claim the app was tested if only static checks ran.

### Phase 10 — Optional deployment after the local demo works

Use a production WSGI server rather than Flask's debug server. Serve the React build and `/api` under one public origin, use HTTPS with secure session cookies, load secrets from deployment configuration, back up MySQL, and reproduce the pinned Python environment. Do not copy the Windows .venv folder to a server. Treat model artifacts as controlled application files. Keep deployment separate from the required local demonstration so it does not delay the project.

**Codex task:** Deploy only after the user has selected the hosting target and requested deployment. First prepare and test the build/run configuration without publishing.

## 9. Local run commands

These application commands become usable after the relevant phases create the files. They are not evidence that the application is already implemented. Run them from the project root in VS Code's PowerShell terminal.

### Existing ML baseline

```powershell
py -3.12 --version
.\.venv\Scripts\python.exe -m unittest discover -s ml\tests -v
.\.venv\Scripts\python.exe ml\05_assess_innings.py --runs 44 --balls 50 --format ODI
```

If the local environment does not yet exist, create it once and install the ML requirements as described in START_HERE.md. Do not recreate it over an environment with a different Python version; create a new one using Python 3.12.

### Backend requirements plan

Codex should start from this dependency set and record exact tested application pins after resolving it. The first line reuses the existing ML pins; paths in nested requirement references are relative to the requirement file.

```text
-r ../ml/requirements.txt
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-Login
Flask-WTF
PyMySQL[rsa]
python-dotenv
pytest
```

Install only after backend/requirements.txt exists:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### Configuration plan

Create backend/.env from backend/.env.example once, then edit local values. Do not overwrite an existing .env containing working values. The factory must explicitly load this file from its project-relative path.

```dotenv
APP_ENV=development
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=mysql+pymysql://cricket_app:replace_password@127.0.0.1:3306/cricket_coach?charset=utf8mb4
TEST_DATABASE_URL=mysql+pymysql://cricket_test:replace_password@127.0.0.1:3306/cricket_coach_test?charset=utf8mb4
```

These are placeholders, not credentials to deploy. Generate a secret locally with `python -c "import secrets; print(secrets.token_hex(32))"` using the project's Python. URL-encode reserved characters in a database password or construct the SQLAlchemy URL from separate environment values. Do not connect as the MySQL root user from the application. Test configuration must require a distinct database ending in `_test` before any destructive reset.

### Migrations and backend startup

Configure Flask-Migrate's directory as backend/migrations in the factory. Run `db init` only once if the migration repository has not already been created. If Codex has committed the initial migration, a new installation needs `db upgrade`, not a new migration.

```powershell
.\.venv\Scripts\python.exe -m flask --app backend.app:create_app db init
.\.venv\Scripts\python.exe -m flask --app backend.app:create_app db migrate -m "Create accounts and batting history"
.\.venv\Scripts\python.exe -m flask --app backend.app:create_app db upgrade
.\.venv\Scripts\python.exe -m flask --app backend.app:create_app run --debug --port 5000
```

The first three commands follow Phase 2; startup is a separate long-running command. Review generated migrations before applying them. Do not run both manual CREATE TABLE SQL and the initial migration against the same empty database: choose migrations as the normal implementation route.

### Frontend setup and startup

From the root, after confirming frontend is still empty, Codex can scaffold:

```powershell
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-router-dom recharts
npm run dev
```

Do not scaffold over an existing implementation. For later installations use `npm ci` with the committed lockfile. Keep Flask running in a separate terminal. Configure Vite approximately as follows, retaining its React plugin:

```javascript
server: {
  port: 5173,
  strictPort: true,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5000',
      changeOrigin: true,
    },
  },
}
```

Open the Vite URL in the browser, normally `http://localhost:5173`. Frontend fetches use `/api/...`, so browser cookies remain on the frontend origin through the development proxy. Do not also hardcode a second backend origin in individual components. Production needs its own same-origin routing; Vite's development proxy is not a production server.

### Tests and build after implementation

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
.\.venv\Scripts\python.exe -m unittest discover -s ml\tests -v
```

Run `npm run build` from the frontend folder. Database integration tests must use the dedicated MySQL test database. Configure fixtures to roll back or reset only test data. Do not rely on backend tests that merely mock away authentication, database ownership or the ML adapter.

## 10. Reference SQL schema

This SQL is a concrete reference for Codex to reproduce in ORM models and migrations. It has not been executed against the user's MySQL server. Migrations are the normal schema authority; do not execute this full table-creation block in addition to applying the initial migration. MySQL-specific constraints must be tested on the selected local server version.

```sql
CREATE DATABASE IF NOT EXISTS cricket_coach
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cricket_coach;

CREATE TABLE users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email VARCHAR(254) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  CONSTRAINT uq_users_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE player_profiles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  display_name VARCHAR(100) NOT NULL,
  club_name VARCHAR(150) NULL,
  batting_hand VARCHAR(10) NOT NULL DEFAULT 'Unknown',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  CONSTRAINT uq_player_profiles_user UNIQUE (user_id),
  CONSTRAINT fk_profiles_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT ck_profiles_hand CHECK (batting_hand IN ('Right','Left','Unknown'))
) ENGINE=InnoDB;

CREATE TABLE matches (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id BIGINT UNSIGNED NOT NULL,
  match_date DATE NOT NULL,
  match_format VARCHAR(10) NOT NULL,
  opposition VARCHAR(150) NULL,
  venue VARCHAR(150) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  INDEX ix_matches_player_format_date (player_id, match_format, match_date, id),
  CONSTRAINT fk_matches_player FOREIGN KEY (player_id)
    REFERENCES player_profiles(id) ON DELETE CASCADE,
  CONSTRAINT ck_matches_format CHECK (match_format IN ('T20','ODI','Test'))
) ENGINE=InnoDB;

CREATE TABLE innings (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  match_id BIGINT UNSIGNED NOT NULL,
  innings_number TINYINT UNSIGNED NOT NULL,
  runs SMALLINT UNSIGNED NOT NULL,
  balls_faced SMALLINT UNSIGNED NOT NULL,
  out_status VARCHAR(10) NOT NULL,
  dismissal_type VARCHAR(20) NOT NULL,
  bowling_length VARCHAR(20) NOT NULL DEFAULT 'Unknown',
  bowling_line VARCHAR(20) NOT NULL DEFAULT 'Unknown',
  shot_type VARCHAR(20) NOT NULL DEFAULT 'Unknown',
  bowler_type VARCHAR(30) NOT NULL DEFAULT 'Unknown',
  notes VARCHAR(1000) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  CONSTRAINT uq_innings_match_number UNIQUE (match_id, innings_number),
  CONSTRAINT fk_innings_match FOREIGN KEY (match_id)
    REFERENCES matches(id) ON DELETE CASCADE,
  CONSTRAINT ck_innings_number CHECK (innings_number BETWEEN 1 AND 4),
  CONSTRAINT ck_innings_status CHECK (out_status IN ('Out','Not Out')),
  CONSTRAINT ck_innings_dismissal CHECK (dismissal_type IN
    ('Caught','Bowled','LBW','Run Out','Stumped','Hit Wicket','Other','Unknown','Not Out')),
  CONSTRAINT ck_innings_status_consistency CHECK (
    (out_status = 'Not Out' AND dismissal_type = 'Not Out') OR
    (out_status = 'Out' AND dismissal_type <> 'Not Out')
  ),
  CONSTRAINT ck_innings_length CHECK (bowling_length IN
    ('Yorker','Full','Good','Short','Bouncer','NA','Unknown')),
  CONSTRAINT ck_innings_line CHECK (bowling_line IN
    ('Outside Off','Off Stump','Middle','Leg Stump','Down Leg','NA','Unknown')),
  CONSTRAINT ck_innings_shot CHECK (shot_type IN
    ('Drive','Cut','Pull','Hook','Sweep','Defensive','Flick','Lofted Shot','Leave','Other','NA','Unknown')),
  CONSTRAINT ck_innings_bowler CHECK (bowler_type IN
    ('Right-arm Fast','Left-arm Fast','Right-arm Medium','Left-arm Medium',
     'Off Spin','Leg Spin','Left-arm Orthodox','Left-arm Wrist Spin','NA','Unknown'))
) ENGINE=InnoDB;
```

The schema's unsigned numeric types enforce storage ranges. The API must additionally validate exact category casing, future dates, format-specific innings rules, context normalization, password requirements and ownership. Server/application connections must use UTC for audit timestamps. SQLAlchemy relationships should be configured consistently with the database deletion behavior; avoid conflicting cascade settings.

The account-deletion cascade is schema behavior for referential integrity, not an instruction to add an account-delete feature to the MVP.

## 11. Instructions to give Codex

Use this prompt at the start of the implementation:

```text
Read README_NEXT_STEPS.md, README.md and START_HERE.md, then inspect the current
repository. Implement only the next unfinished phase from README_NEXT_STEPS.md.

Preserve the existing ml/ package, source dataset, model artifacts and research
limitations. Do not retrain, change the target, invent model accuracy or replace
the analysis with mock data. Use React/Vite, Flask, MySQL and the cookie-session
authentication approach specified in the guide.

Use authenticated database history with analyze_history(), not the Excel-reading
analyze_player(). Enforce the five-innings requirement within the selected format.
Do not pass performance_label=None and do not trust a client-supplied player ID.

Complete that phase's acceptance checks. Report changed files, exact Windows
commands, actual test results and any remaining blockers. Update the phase status
in this README only after the work is verified. Do not mark later phases complete.
```

Suggested phase tracker to maintain in the repository:

| Phase | Initial status | Evidence to add when completed |
|---|---|---|
| 0. Baseline | Pending local confirmation | Versions, ML checks and assessment command |
| 1. Backend foundation | Not started | Startup and health/readiness responses |
| 2. Database | Not started | Migration revision and MySQL constraint checks |
| 3. Authentication | Not started | Session, CSRF and ownership identity tests |
| 4. Innings CRUD | Not started | Validation and two-user isolation checks |
| 5. ML integration | Not started | New account, five records and live analysis response |
| 6. Frontend authentication | Not started | Browser login/logout/refresh checks |
| 7. Records UI | Not started | Create/edit/delete against MySQL |
| 8. Dashboard | Not started | Real charts, supported tips and empty states |
| 9. End-to-end demo | Not started | Test results, build and complete demo run |
| 10. Deployment | Optional later | Hosting-specific verified release steps |

If a phase is already implemented when Codex starts, verify it against the guide rather than overwriting working code. Use small commits per phase. If an implementation decision must differ from this guide, document the concrete reason and update the affected schema/API sections together.

## 12. Definition of completion and references

The first application version is complete when a fresh player account can register, log in, add at least five valid same-format innings through the browser, and see form, supporting dismissal patterns where available, and relevant tips. The history must persist after logout/restart, edits and deletions must affect subsequent analysis, and another account must not access or influence that private history.

The software demonstration and research validation are separate. Keep the existing classifier comparison, rubric baseline, dataset provenance and limitations in the academic report. The system must not present its prototype tips as proven technical diagnoses or claim that the classifier's accuracy validates all dashboard outputs.

Official implementation references:

- Flask application factories: https://flask.palletsprojects.com/en/stable/patterns/appfactories/
- Flask-Login session management: https://flask-login.readthedocs.io/en/latest/
- Flask-WTF CSRF protection: https://flask-wtf.readthedocs.io/en/1.2.x/csrf/
- Flask-Migrate migrations: https://flask-migrate.readthedocs.io/en/latest/
- MySQL CHECK constraints: https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html
- Vite development server/proxy: https://vite.dev/config/server-options.html
- Scikit-learn model persistence: https://scikit-learn.org/stable/model_persistence.html

Prepared against the latest reviewed project on 28 October 2026. This guide is the proposed application handover; implementation phases must supply their own actual validation evidence.

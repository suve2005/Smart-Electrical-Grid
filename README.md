# Smart Electrical Grid

FastAPI backend and LankaGrid authentication frontend for the Smart Electrical Grid application.

## Architecture

- Firebase Authentication owns user identity, passwords, email verification and sign-in.
- FastAPI verifies Firebase ID tokens using the Firebase Admin SDK.
- PostgreSQL is the authoritative store for application profiles and roles.
- SQLAlchemy maps the two application tables: app_users and roles.
- NIC and employee ID values are stored as salted PBKDF2-HMAC-SHA256 hashes.
- Passwords and raw NIC / employee ID values are never stored in PostgreSQL or returned by the API.

New accounts receive the Engineer role. Only an Admin can change a user's role or active status. The registration form does not allow users to assign themselves a role.

## Authentication and profile flow

1. Registration creates a Firebase Authentication account.
2. The frontend obtains that account's Firebase ID token and sends the full name, email, NIC, employee ID and token to POST /api/v1/auth/register.
3. FastAPI verifies the token, hashes NIC and employee ID, and creates the app_users row with the default Engineer role.
4. Firebase sends the email-verification message. The frontend signs the user out until the email is verified.
5. Login verifies Firebase credentials in the browser, then sends the ID token to POST /api/v1/auth/login. FastAPI checks the token, matching PostgreSQL profile and active status.
6. The dashboard sends the Firebase ID token as a Bearer token to GET /api/v1/auth/me. The profile shown comes from PostgreSQL, not Firestore.

Firebase Authentication handles login and logout. The logout API route is only an acknowledgement; client-side Firebase signOut() ends the browser session.

## Relevant project structure

- app/main.py — FastAPI application and CORS middleware
- app/core/config.py — repository-root .env settings
- app/core/deps.py — Firebase Admin token verification and current-user / Admin dependencies
- app/core/security.py — PBKDF2 identifier hashing
- app/db/session.py — SQLAlchemy database session
- app/models/ — app_users and roles ORM models
- app/api/v1/endpoints.py — registration, login, current profile and Admin user-management routes
- app/api/v1/schemas.py — API request and response contracts
- alembic/ — database migrations
- FrontEnd/lankagrid-auth/ — plain HTML, CSS and JavaScript authentication interface

## Configuration

Copy .env.example to .env and set the local PostgreSQL connection values used by Docker Compose.

For Firebase token verification, configure Firebase Admin credentials. Download a service-account JSON file for the same Firebase project and set FIREBASE_SERVICE_ACCOUNT_PATH in the local .env. Keep that JSON file private and never commit it. On environments with Google Application Default Credentials configured, the service-account path can be omitted.

The browser Firebase web configuration is in FrontEnd/lankagrid-auth/js/auth.js. The frontend API URL defaults to http://127.0.0.1:8000; set window.LANKAGRID_API_BASE_URL before the frontend module scripts load to override it.

CORS_ORIGINS must include the frontend's origin. The default FastAPI development origins include localhost and 127.0.0.1 on ports 5500, 5501 and 3000.

## API routes

All authentication and profile routes are under /api/v1/auth:

| Method | Route | Purpose |
| --- | --- | --- |
| POST | /register | Verify a new Firebase account and create its PostgreSQL profile |
| POST | /login | Verify Firebase ID token and validate the PostgreSQL profile |
| POST | /refresh | Revalidate the Firebase token and profile |
| POST | /logout | Acknowledge client-side Firebase sign-out |
| GET | /me | Return the authenticated user's PostgreSQL profile |
| GET | /users | List users (Admin only) |
| GET | /users/{user_id} | Get a user (Admin only) |
| PATCH | /users/{user_id}/role | Change Engineer / Admin role (Admin only) |
| PATCH | /users/{user_id}/status | Activate or deactivate a user (Admin only) |

The public UserResponse deliberately excludes employee_id_hash and nic_hash.

## Local frontend

Open FrontEnd/lankagrid-auth with VS Code Live Server. The usual Live Server origin, http://127.0.0.1:5500, is allowed by the development CORS defaults. Run FastAPI separately at http://127.0.0.1:8000.

The backend is not responsible for implementing grid telemetry, simulation, forecasting or dashboard functionality. Those remain separate project work owned by the relevant teammates.

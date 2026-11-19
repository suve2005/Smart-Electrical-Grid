# Smart-Electrical-Grid

FastAPI backend for the Smart Electrical Grid application with Firebase Authentication and Postgres database.

## Architecture

**Authentication/Authorization Separation:**
- **Firebase Authentication** handles user authentication (ID token verification)
- **FastAPI backend** handles authorization (role-based access control, user management)

**Database:** Postgres via SQLAlchemy ORM
**Security:** PBKDF2-HMAC-SHA256 hashing for NIC and employee_id fields
**Two-table schema:** `app_users` + `roles`

## Key Features

- ✅ Firebase Auth integration (mock API key initially, upgradable to real Firebase project)
- ✅ PBKDF2-HMAC-SHA256 hashing for NIC and employee_id (100k iterations, 16-byte salts)
- ✅ No passwords stored in Postgres (Firebase handles auth)
- ✅ Role-based access control (Engineer default, Admin promotion)
- ✅ Complete user management endpoints
- ✅ Structured security event logging

## Project Structure

```
Smart-Electrical-Grid/
├── app/
│   ├── core/           # Config, security, dependencies
│   │   ├── config.py       # Environment variables
│   │   ├── security.py     # PBKDF2 hashing + mock Firebase token verification
│   │   └── deps.py         # FastAPI dependencies (get_current_user, require_admin)
│   ├── db/               # Database session and models
│   │   ├── session.py      # get_db() dependency, SessionLocal, engine
│   │   └── base.py         # Declarative Base
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py         # app_users table (firebase_uid, employee_id_hash, nic_hash, role_id, is_active)
│   │   └── role.py         # roles table (role_id, role_name)
│   ├── api/              # Route endpoints
│   │   ├── v1/
│   │   │   ├── endpoints.py  # All auth + user management endpoints
│   │   │   └── schemas.py    # Pydantic models (RegisterRequest, LoginRequest, UserResponse, etc.)
│   └── main.py           # FastAPI app entry point
├── alembic/              # Database migrations
├── .env                  # Configuration secrets
└── requirements.txt      # Python dependencies
```

## Authentication Flow

```
POST /auth/register
  → Verify Firebase ID token (mock → real Firebase)
  → Hash NIC and employee_id using PBKDF2-HMAC-SHA256
  → Look up/create default Engineer role
  → Create app_users record in Postgres
  → Return AuthResponse with user info

POST /auth/login
  → Verify Firebase ID token
  → Look up user by email in app_users
  → Check is_active status
  → Return AuthResponse with user info

GET /auth/me
  → Uses get_current_user dependency
  → Verify Firebase token from Authorization header
  → Look up user by firebase_uid
  → Check is_active status
  → Return UserResponse

GET/POST /auth/users/{id}/role  (admin only)
  → Admin can promote/demote users between Engineer and Admin

GET/POST /auth/users/{id}/status (admin only)
  → Admin can activate/deactivate user accounts
```

## Endpoints

### Auth Endpoints (all under `/api/v1/auth` prefix)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register new user | None (Firebase token in body) |
| POST | `/login` | Login with Firebase token | None |
| POST | `/refresh` | Refresh session | None |
| POST | `/logout` | Logout user | None |
| GET | `/me` | Get current user profile | ✅ Firebase token |
| GET | `/users` | List all users | ✅ Admin only |
| GET | `/users/{id}` | Get user by ID | ✅ Admin only |
| PATCH | `/users/{id}/role` | Change user role | ✅ Admin only |
| PATCH | `/users/{id}/status` | Change user status | ✅ Admin only |

### Security

- **PBKDF2-HMAC-SHA256** with 100,000 iterations and 16-byte random salts
- **Stored format:** `{salt_base64}:{hash_base64}`
- **Sensitive fields:** `nic_hash`, `employee_id_hash` (no plaintext in DB or API responses)
- **Token verification:** Mock initially (tokens starting with `mock-`), upgrade to real `firebase_admin.auth.verify_id_token()`

### Configuration

Create `.env` file:

```env
# Firebase (mock initially)
FIREBASE_API_KEY=mock_key_for_development
FIREBASE_AUTH_DOMAIN=mock-project.firebaseapp.com

# Database
DATABASE_URL=postgresql://postgres:password@localhost/smart_grid

# Security
SECRET_KEY=change-this-in-production
PBKDF2_ITERATIONS=100000
SALT_BYTES=16
```

### Running the Application

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up database
# Ensure Postgres is running, then create the database
createdb smart_grid
alembic upgrade head

# 3. Start the server
uvicorn app.main:app --reload

# 4. The server will be available at http://127.0.0.1:8000
# API docs at http://127.0.0.1:8000/docs
```

### Development

```bash
# Run with auto-reload (default)
uvicorn app.main:app --reload

# Run with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Access API documentation at /docs
# Access alternative docs at /redoc
```

### Testing

The project includes registered test patterns:

- Register endpoint with valid/invalid data
- Login with verified Firebase token
- NIC/employee_id hashing and verification
- Role assignment defaults to Engineer
- Endpoint responses and error handling

### Production Upgrade Path

When ready to use real Firebase:

1. Replace `FIREBASE_API_KEY` in `.env` with real Firebase API key
2. Replace `verify_firebase_token_mock()` call in `core/deps.py` with:
   ```python
   import firebase_admin
   from firebase_admin import auth
   return auth.verify_id_token(id_token)
   ```
3. Ensure proper Firebase project setup with Authentication enabled

### Memory & Status Tracking

Audit fix status and implementation details are tracked in:
- `memory/fixes-status.md` - Complete list of all fixes applied
- `memory/audit-completion-final.md` - Final audit report
- `memory/final-summary.md` - Project summary

### Code Review & Quality

All 13 audit fix items implemented:
- ✅ 3 CRITICAL: Frontend UID trust, employee_id_hash, schema field names
- ✅ 6 HIGH: Auth middleware, 5 missing endpoints + role/status endpoints
- ✅ 3 MEDIUM: List import, enhanced token verification, role validation

The backend is now complete and ready for front-end client integration using Firebase Authentication.
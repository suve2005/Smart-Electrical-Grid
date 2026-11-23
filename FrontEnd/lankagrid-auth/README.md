# LankaGrid – Authentication UI

Plain HTML, CSS and vanilla JavaScript. No framework or build step is required.

## Run it

Serve this folder over HTTP; ES modules do not load from file://. Use VS Code Live Server (normally http://127.0.0.1:5500) and ensure FastAPI is running at http://127.0.0.1:8000.

## Authentication and profiles

- Firebase Authentication handles email/password and Google identity.
- The browser sends the Firebase ID token to FastAPI.
- FastAPI verifies the token with the Firebase Admin SDK.
- PostgreSQL is the only source of application profile data.
- Firestore is not used for user profiles.
- New profiles are assigned the Engineer role by the backend. Users cannot grant themselves the Admin role.
- NIC and employee ID are sent only to the registration endpoint; FastAPI stores salted PBKDF2 hashes. Passwords remain in Firebase Authentication.

The backend API defaults to http://127.0.0.1:8000. To override it, set window.LANKAGRID_API_BASE_URL before the page's module scripts load. The backend CORS_ORIGINS setting must include the frontend origin.

## Structure

index.html       Login page
register.html    Registration page
dashboard.html  Authenticated dashboard
css/styles.css   Theme, layout and components
js/theme.js      Theme toggle
js/ui.js         Form validation and UI helpers
js/auth.js       Firebase auth and FastAPI API client
js/login.js      Login page controller
js/register.js   Registration page controller
js/guard.js      Firebase-authenticated page guard
js/dashboard.js  Loads the PostgreSQL profile through FastAPI
assets/          Logo and illustration assets

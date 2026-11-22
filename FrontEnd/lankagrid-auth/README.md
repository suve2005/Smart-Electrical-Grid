# LankaGrid – Authentication UI

Plain HTML, CSS and vanilla JS. No frameworks, no build step.

## Run it
ES modules do not load from `file://`, so serve the folder over HTTP:
- VS Code: right-click `index.html` -> "Open with Live Server", or
- Terminal: `python3 -m http.server 8000` then open http://localhost:8000

## Structure
index.html       login page (markup only)
register.html    registration page (markup only)
dashboard.html   authenticated dashboard (protected by js/guard.js)
css/styles.css   design tokens (light/dark), layout, components
js/theme.js      dark/light toggle (persisted, follows OS until changed)
js/ui.js         validation, password strength, show/hide password, alerts
js/auth.js       Firebase initialization and authentication functions
js/login.js      connects index.html to ui.js + auth.js
js/register.js   connects register.html to ui.js + auth.js
js/guard.js      redirects unauthenticated or unverified dashboard visitors
js/dashboard.js  loads the Firestore profile and handles sign-out
assets/          logo + placeholder hero art (replace with real photos)

New email/password accounts must verify their email before signing in. The
dashboard displays the profile stored at `users/{uid}`; account roles are
assigned server-side, and new profiles default to `viewer`.

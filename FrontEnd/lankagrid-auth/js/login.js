/* ==========================================================================
   login.js – wires index.html to ui.js (validation) and auth.js (hooks)
   ========================================================================== */
import {
  validators,
  bindValidation,
  setFieldState,
  setLoading,
  showAlert,
  hideAlert,
  initPasswordToggles,
} from './ui.js';
import {
  auth,
  onAuthStateChanged,
  handleLogin,
  handleGoogle,
  handleForgotPassword,
  DEMO_MODE,
} from './auth.js';

let checkedInitialAuthState = false;
onAuthStateChanged(auth, (user) => {
  if (checkedInitialAuthState) return;
  checkedInitialAuthState = true;

  if (user && user.emailVerified) {
    window.location.replace('dashboard.html');
  }
});

const form = document.getElementById('login-form');
const alertEl = document.getElementById('form-alert');
const submitBtn = document.getElementById('submit-btn');
const googleBtn = document.getElementById('google-btn');
const forgotBtn = document.getElementById('forgot-btn');
const emailEl = form.elements.email;

initPasswordToggles(form);

const validation = bindValidation(form, {
  email: validators.email,
  password: validators.passwordRequired,
});

let busy = false; // blocks double submits across all actions

/** Run an async action with loading + error handling. */
async function run(button, loadingText, action) {
  if (busy) return;
  busy = true;
  hideAlert(alertEl);
  setLoading(button, true, loadingText);
  try {
    const result = await action();
    if (result && result.redirectTo) {
      window.location.assign(result.redirectTo);
      return;
    }
    return result;
  } catch (err) {
    showAlert(alertEl, 'error', (err && err.message) || 'Something went wrong. Please try again.');
  } finally {
    busy = false;
    setLoading(button, false, loadingText);
  }
}

/* Sign in */
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy || !validation.validate()) return;

  const result = await run(submitBtn, 'Signing in…', () =>
    handleLogin(emailEl.value.trim(), form.elements.password.value, form.elements.remember.checked)
  );
  if (result) {
    showAlert(
      alertEl,
      'success',
      DEMO_MODE
        ? 'Demo mode: the form is valid and handleLogin() was called. Connect Firebase in js/auth.js.'
        : 'Signed in successfully.'
    );
  }
});

/* Continue with Google */
googleBtn.addEventListener('click', async () => {
  const result = await run(googleBtn, 'Connecting…', () => handleGoogle());
  if (result) {
    showAlert(
      alertEl,
      'success',
      DEMO_MODE
        ? 'Demo mode: handleGoogle() was called. Connect Firebase in js/auth.js.'
        : 'Signed in with Google.'
    );
  }
});

/* Forgot password: needs a valid email first */
forgotBtn.addEventListener('click', async () => {
  hideAlert(alertEl);
  const message = validators.email(emailEl);
  setFieldState(emailEl, message);
  if (message) {
    emailEl.focus();
    return;
  }
  const result = await run(forgotBtn, null, () => handleForgotPassword(emailEl.value.trim()));
  if (result) {
    // Generic wording on purpose: never reveal whether an account exists.
    showAlert(alertEl, 'success', 'If an account exists for that email, a password reset link has been sent.');
  }
});

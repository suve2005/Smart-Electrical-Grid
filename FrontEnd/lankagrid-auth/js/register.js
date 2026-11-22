/* ==========================================================================
   register.js – wires register.html to ui.js (validation) and auth.js (hooks)
   ========================================================================== */
import {
  validators,
  bindValidation,
  setLoading,
  showAlert,
  hideAlert,
  initPasswordToggles,
  initPasswordStrength,
} from './ui.js';
import { auth, onAuthStateChanged, handleRegister } from './auth.js';

let checkedInitialAuthState = false;
onAuthStateChanged(auth, (user) => {
  if (checkedInitialAuthState) return;
  checkedInitialAuthState = true;

  if (user && user.emailVerified) {
    window.location.replace('dashboard.html');
  }
});

const form = document.getElementById('register-form');
const alertEl = document.getElementById('form-alert');
const submitBtn = document.getElementById('submit-btn');
const registerView = document.getElementById('register-view');
const successView = document.getElementById('success-view');
const successTitle = document.getElementById('success-title');
const successEmail = document.getElementById('success-email');

initPasswordToggles(form);

initPasswordStrength({
  input: form.elements.password,
  meter: document.getElementById('strength'),
  textEl: document.getElementById('strength-text'),
  rulesList: document.getElementById('password-rules'),
});

const validation = bindValidation(
  form,
  {
    fullname: validators.fullName,
    email: validators.email,
    password: validators.newPassword,
    confirm: validators.confirmPassword,
    role: validators.role,
    terms: validators.terms,
  },
  // Re-check "confirm" whenever the password changes
  { password: ['confirm'] }
);

let busy = false;

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy) return;
  hideAlert(alertEl);
  if (!validation.validate()) return;

  busy = true;
  setLoading(submitBtn, true, 'Creating account…');

  const email = form.elements.email.value.trim();
  try {
    await handleRegister({
      name: form.elements.fullname.value.trim(),
      email,
      password: form.elements.password.value,
      role: form.elements.role.value, // a REQUEST only; assign real roles server-side
    });

    // Success state
    successEmail.textContent = email;
    registerView.hidden = true;
    successView.hidden = false;
    form.reset();
    successTitle.focus();
  } catch (err) {
    showAlert(alertEl, 'error', (err && err.message) || 'We could not create your account. Please try again.');
  } finally {
    busy = false;
    setLoading(submitBtn, false, 'Creating account…');
  }
});

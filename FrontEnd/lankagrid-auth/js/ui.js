/* ==========================================================================
   ui.js – validation + UI helpers shared by login.js and register.js
   No backend logic here. Never log or store passwords in this file.
   ========================================================================== */

/* ---------- Validation rules ---------- */

export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export const PASSWORD_RULES = [
  { id: 'length', test: (v) => v.length >= 8 },
  { id: 'upper',  test: (v) => /[A-Z]/.test(v) },
  { id: 'lower',  test: (v) => /[a-z]/.test(v) },
  { id: 'number', test: (v) => /\d/.test(v) },
  { id: 'symbol', test: (v) => /[^A-Za-z0-9]/.test(v) },
];

/**
 * Field validators. Each takes (element, form) and returns an error message,
 * or an empty string when the field is valid.
 */
export const validators = {
  email(el) {
    const v = el.value.trim();
    if (!v) return 'Enter your email address.';
    return EMAIL_RE.test(v) ? '' : 'Enter a valid email address.';
  },

  /** Login only needs "not empty"; the strength rules apply on registration. */
  passwordRequired(el) {
    return el.value ? '' : 'Enter your password.';
  },

  fullName(el) {
    const v = el.value.trim();
    if (!v) return 'Enter your full name.';
    return v.length >= 2 ? '' : 'Name must be at least 2 characters.';
  },

  newPassword(el) {
    if (!el.value) return 'Create a password.';
    return PASSWORD_RULES.every((r) => r.test(el.value))
      ? ''
      : 'Password must meet all the requirements below.';
  },

  confirmPassword(el, form) {
    if (!el.value) return 'Confirm your password.';
    return el.value === form.elements.password.value ? '' : 'Passwords do not match.';
  },

  role(el) {
    return el.value ? '' : 'Select a role.';
  },

  terms(el) {
    return el.checked ? '' : 'You must accept the Terms of Service and Privacy Policy.';
  },
};

/* ---------- Field state ---------- */

/** Show (message) or clear ('') the validation state of a single control. */
export function setFieldState(el, message) {
  const field = el.closest('.field');
  const errorEl = field && field.querySelector('.field-error');
  if (!field || !errorEl) return;

  if (message) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    el.setAttribute('aria-invalid', 'true');
    errorEl.textContent = message;
  } else {
    field.classList.remove('is-invalid');
    const hasValue = el.type === 'checkbox' ? false : el.value.trim() !== '';
    field.classList.toggle('is-valid', hasValue);
    el.removeAttribute('aria-invalid');
    errorEl.textContent = '';
  }
}

/**
 * Wire inline validation to a form.
 *  - schema: { fieldName: validatorFn }
 *  - links:  { fieldName: [otherFields to re-check when it changes] }
 * Validates on blur; after a field has been touched it re-validates live.
 * Returns { validate() } where validate() checks everything, focuses the
 * first invalid control and returns true/false.
 */
export function bindValidation(form, schema, links = {}) {
  const touched = new Set();
  const names = Object.keys(schema);

  const run = (name) => {
    const el = form.elements[name];
    const message = schema[name](el, form);
    setFieldState(el, message);
    return !message;
  };

  names.forEach((name) => {
    const el = form.elements[name];
    const discrete = el.type === 'checkbox' || el.tagName === 'SELECT';

    el.addEventListener('blur', () => {
      touched.add(name);
      run(name);
    });

    el.addEventListener(discrete ? 'change' : 'input', () => {
      if (discrete) touched.add(name);
      if (touched.has(name)) run(name);
      (links[name] || []).forEach((dep) => touched.has(dep) && run(dep));
    });
  });

  return {
    validate() {
      let firstInvalid = null;
      names.forEach((name) => {
        touched.add(name);
        if (!run(name) && !firstInvalid) firstInvalid = form.elements[name];
      });
      if (firstInvalid) firstInvalid.focus();
      return !firstInvalid;
    },
  };
}

/* ---------- Buttons + alerts ---------- */

/** Toggle the loading state (disables the button and shows the spinner). */
export function setLoading(btn, isLoading, loadingText) {
  const label = btn.querySelector('.btn-label');
  if (label && !btn.dataset.label) btn.dataset.label = label.textContent;

  btn.disabled = isLoading;
  btn.classList.toggle('is-loading', isLoading);
  btn.setAttribute('aria-busy', String(isLoading));

  if (label && loadingText) {
    label.textContent = isLoading ? loadingText : btn.dataset.label;
  }
}

/** Show a form-level message. type: 'error' | 'success' */
export function showAlert(el, type, message) {
  el.className = `alert alert--${type}`;
  el.textContent = message; // textContent (never innerHTML) – safe for any text
  el.hidden = false;
}

export function hideAlert(el) {
  el.hidden = true;
  el.textContent = '';
}

/* ---------- Password helpers ---------- */

/** Show / hide password buttons: <button data-toggle-password="inputId"> */
export function initPasswordToggles(root = document) {
  root.querySelectorAll('[data-toggle-password]').forEach((btn) => {
    const input = document.getElementById(btn.dataset.togglePassword);
    if (!input) return;
    btn.addEventListener('click', () => {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-pressed', String(show));
    });
  });
}

/** Strength meter + rules checklist for the register password field. */
export function initPasswordStrength({ input, meter, textEl, rulesList }) {
  const WORDS = { none: '—', weak: 'Weak', medium: 'Medium', strong: 'Strong' };

  const update = () => {
    const value = input.value;
    const results = PASSWORD_RULES.map((r) => r.test(value));
    const score = results.filter(Boolean).length;

    let level = 'none';
    if (value) {
      if (!results[0]) level = 'weak';          // under 8 chars is always weak
      else if (score === PASSWORD_RULES.length) level = 'strong';
      else if (score >= 3) level = 'medium';
      else level = 'weak';
    }

    meter.dataset.level = level;
    if (textEl.textContent !== WORDS[level]) textEl.textContent = WORDS[level];

    PASSWORD_RULES.forEach((rule, i) => {
      const li = rulesList.querySelector(`[data-rule="${rule.id}"]`);
      if (!li) return;
      li.classList.toggle('is-met', results[i]);
      const status = li.querySelector('[data-status]');
      if (status) status.textContent = results[i] ? ' (met)' : ' (not met)';
    });
  };

  input.addEventListener('input', update);
  update();
}

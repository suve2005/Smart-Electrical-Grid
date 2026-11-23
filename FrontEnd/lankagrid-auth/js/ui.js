/* Shared validation and UI helpers. No backend logic or password storage. */

export const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export const PASSWORD_RULES = [
  { id: "length", test: (value) => value.length >= 8 },
  { id: "upper", test: (value) => /[A-Z]/.test(value) },
  { id: "lower", test: (value) => /[a-z]/.test(value) },
  { id: "number", test: (value) => /\d/.test(value) },
  { id: "symbol", test: (value) => /[^A-Za-z0-9]/.test(value) },
];

export const validators = {
  email(element) {
    const value = element.value.trim();
    if (!value) return "Enter your email address.";
    return EMAIL_RE.test(value) ? "" : "Enter a valid email address.";
  },
  passwordRequired(element) {
    return element.value ? "" : "Enter your password.";
  },
  fullName(element) {
    const value = element.value.trim();
    if (!value) return "Enter your full name.";
    return value.length >= 2 ? "" : "Name must be at least 2 characters.";
  },
  nic(element) {
    const value = element.value.trim();
    if (!value) return "Enter your NIC number.";
    return value.length >= 5 && value.length <= 20 ? "" : "Enter a valid NIC number.";
  },
  employeeId(element) {
    const value = element.value.trim();
    if (!value) return "Enter your employee ID.";
    return value.length <= 50 ? "" : "Employee ID must be 50 characters or fewer.";
  },
  newPassword(element) {
    if (!element.value) return "Create a password.";
    return PASSWORD_RULES.every((rule) => rule.test(element.value))
      ? ""
      : "Password must meet all the requirements below.";
  },
  confirmPassword(element, form) {
    if (!element.value) return "Confirm your password.";
    return element.value === form.elements.password.value ? "" : "Passwords do not match.";
  },
  terms(element) {
    return element.checked ? "" : "You must accept the Terms of Service and Privacy Policy.";
  },
};

export function setFieldState(element, message) {
  const field = element.closest(".field");
  const errorElement = field && field.querySelector(".field-error");
  if (!field || !errorElement) return;
  if (message) {
    field.classList.add("is-invalid");
    field.classList.remove("is-valid");
    element.setAttribute("aria-invalid", "true");
    errorElement.textContent = message;
  } else {
    field.classList.remove("is-invalid");
    const hasValue = element.type === "checkbox" ? false : element.value.trim() !== "";
    field.classList.toggle("is-valid", hasValue);
    element.removeAttribute("aria-invalid");
    errorElement.textContent = "";
  }
}

export function bindValidation(form, schema, links = {}) {
  const touched = new Set();
  const names = Object.keys(schema);
  const run = (name) => {
    const element = form.elements[name];
    const message = schema[name](element, form);
    setFieldState(element, message);
    return !message;
  };

  names.forEach((name) => {
    const element = form.elements[name];
    const discrete = element.type === "checkbox" || element.tagName === "SELECT";
    element.addEventListener("blur", () => {
      touched.add(name);
      run(name);
    });
    element.addEventListener(discrete ? "change" : "input", () => {
      if (discrete) touched.add(name);
      if (touched.has(name)) run(name);
      (links[name] || []).forEach((dependency) => {
        if (touched.has(dependency)) run(dependency);
      });
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

export function setLoading(button, isLoading, loadingText) {
  const label = button.querySelector(".btn-label");
  if (label && !button.dataset.label) button.dataset.label = label.textContent;
  button.disabled = isLoading;
  button.classList.toggle("is-loading", isLoading);
  button.setAttribute("aria-busy", String(isLoading));
  if (label && loadingText) label.textContent = isLoading ? loadingText : button.dataset.label;
}

export function showAlert(element, type, message) {
  element.className = "alert alert--" + type;
  element.textContent = message;
  element.hidden = false;
}

export function hideAlert(element) {
  element.hidden = true;
  element.textContent = "";
}

export function initPasswordToggles(root = document) {
  root.querySelectorAll("[data-toggle-password]").forEach((button) => {
    const input = document.getElementById(button.dataset.togglePassword);
    if (!input) return;
    button.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      button.setAttribute("aria-pressed", String(show));
    });
  });
}

export function initPasswordStrength({ input, meter, textEl, rulesList }) {
  const words = { none: "—", weak: "Weak", medium: "Medium", strong: "Strong" };
  const update = () => {
    const results = PASSWORD_RULES.map((rule) => rule.test(input.value));
    const score = results.filter(Boolean).length;
    let level = "none";
    if (input.value) {
      if (!results[0]) level = "weak";
      else if (score === PASSWORD_RULES.length) level = "strong";
      else if (score >= 3) level = "medium";
      else level = "weak";
    }
    meter.dataset.level = level;
    textEl.textContent = words[level];
    PASSWORD_RULES.forEach((rule, index) => {
      const item = rulesList.querySelector('[data-rule="' + rule.id + '"]');
      if (!item) return;
      item.classList.toggle("is-met", results[index]);
      const status = item.querySelector("[data-status]");
      if (status) status.textContent = results[index] ? " (met)" : " (not met)";
    });
  };
  input.addEventListener("input", update);
  update();
}

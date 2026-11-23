/* Register form wiring. Firebase creates the identity; FastAPI stores the profile. */

import {
  validators,
  bindValidation,
  setLoading,
  showAlert,
  hideAlert,
  initPasswordToggles,
  initPasswordStrength,
} from "./ui.js";
import { auth, onAuthStateChanged, handleRegister } from "./auth.js";

let checkedInitialAuthState = false;
onAuthStateChanged(auth, (user) => {
  if (checkedInitialAuthState) return;
  checkedInitialAuthState = true;
  if (user && user.emailVerified) {
    window.location.replace("dashboard.html");
  }
});

const form = document.getElementById("register-form");
const alertEl = document.getElementById("form-alert");
const submitBtn = document.getElementById("submit-btn");
const registerView = document.getElementById("register-view");
const successView = document.getElementById("success-view");
const successTitle = document.getElementById("success-title");
const successEmail = document.getElementById("success-email");

// The database schema requires both identifiers. Insert them using the
// existing form styles, and remove the old client-selectable role control.
function addProfileField(name, id, labelText, placeholder, maxLength, afterField) {
  const field = document.createElement("div");
  field.className = "field";

  const label = document.createElement("label");
  label.className = "sr-only";
  label.htmlFor = id;
  label.textContent = labelText;

  const inputWrap = document.createElement("div");
  inputWrap.className = "input-wrap";

  const input = document.createElement("input");
  input.id = id;
  input.name = name;
  input.type = "text";
  input.autocomplete = "off";
  input.placeholder = placeholder;
  input.required = true;
  input.maxLength = maxLength;
  input.setAttribute("aria-describedby", id + "-error");

  const error = document.createElement("p");
  error.className = "field-error";
  error.id = id + "-error";
  error.setAttribute("aria-live", "polite");

  inputWrap.append(input);
  field.append(label, inputWrap, error);
  afterField.after(field);
  return field;
}

const roleField = form.elements.role && form.elements.role.closest(".field");
if (roleField) roleField.remove();

const emailField = form.elements.email.closest(".field");
const nicField = addProfileField("nic", "nic", "NIC number", "NIC Number", 20, emailField);
addProfileField("employee_id", "employee_id", "Employee ID", "Employee ID", 50, nicField);

initPasswordToggles(form);
initPasswordStrength({
  input: form.elements.password,
  meter: document.getElementById("strength"),
  textEl: document.getElementById("strength-text"),
  rulesList: document.getElementById("password-rules"),
});

const validation = bindValidation(
  form,
  {
    fullname: validators.fullName,
    email: validators.email,
    nic: validators.nic,
    employee_id: validators.employeeId,
    password: validators.newPassword,
    confirm: validators.confirmPassword,
    terms: validators.terms,
  },
  { password: ["confirm"] }
);

let busy = false;
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  hideAlert(alertEl);
  if (!validation.validate()) return;

  busy = true;
  setLoading(submitBtn, true, "Creating account…");
  const email = form.elements.email.value.trim();

  try {
    await handleRegister({
      name: form.elements.fullname.value.trim(),
      email,
      password: form.elements.password.value,
      nic: form.elements.nic.value.trim(),
      employeeId: form.elements.employee_id.value.trim(),
    });

    successEmail.textContent = email;
    registerView.hidden = true;
    successView.hidden = false;
    form.reset();
    successTitle.focus();
  } catch (error) {
    showAlert(
      alertEl,
      "error",
      (error && error.message) || "We could not create your account. Please try again."
    );
  } finally {
    busy = false;
    setLoading(submitBtn, false, "Creating account…");
  }
});

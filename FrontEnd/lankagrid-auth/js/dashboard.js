import {
  auth,
  onAuthStateChanged,
  signOut,
  getCurrentUserProfile,
} from "./auth.js";

const nameEl = document.getElementById("user-name");
const emailEl = document.getElementById("user-email");
const roleEl = document.getElementById("user-role");
const alertEl = document.getElementById("dashboard-alert");
const signOutButton = document.getElementById("signout-btn");

function showError(message, error) {
  alertEl.textContent = message;
  alertEl.hidden = false;
  if (error) console.error(message, error);
}

async function loadProfile(user) {
  try {
    const response = await getCurrentUserProfile(user);
    const profile = response.user || response;
    nameEl.textContent = profile.fullname || user.displayName || "—";
    emailEl.textContent = profile.email || user.email || "—";
    roleEl.textContent =
      profile.role && profile.role.role_name
        ? profile.role.role_name
        : "Unavailable";

    if (roleEl.textContent === "Unavailable") {
      showError("Your PostgreSQL profile does not have a role. Please contact an administrator.");
    }
  } catch (error) {
    nameEl.textContent = user.displayName || "—";
    emailEl.textContent = user.email || "—";
    roleEl.textContent = "Unavailable";
    showError(error.message || "We could not load your profile from the backend.", error);
  }
}

onAuthStateChanged(auth, (user) => {
  if (!user || !user.emailVerified) return;
  nameEl.textContent = user.displayName || "—";
  emailEl.textContent = user.email || "—";
  roleEl.textContent = "Loading…";
  loadProfile(user);
});

signOutButton.addEventListener("click", async () => {
  signOutButton.disabled = true;
  signOutButton.setAttribute("aria-busy", "true");
  try {
    await signOut(auth);
    window.location.replace("index.html");
  } catch (error) {
    showError("We could not sign you out. Please try again.", error);
    signOutButton.disabled = false;
    signOutButton.removeAttribute("aria-busy");
  }
});

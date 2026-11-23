/* Firebase Authentication plus the FastAPI/PostgreSQL profile API. */

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.0/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged,
  createUserWithEmailAndPassword,
  updateProfile,
  sendEmailVerification,
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  sendPasswordResetEmail,
  setPersistence,
  browserLocalPersistence,
  browserSessionPersistence,
  signOut,
} from "https://www.gstatic.com/firebasejs/11.0.0/firebase-auth.js";

export const DEMO_MODE = false;
const AFTER_LOGIN_URL = "dashboard.html";

// Override before module scripts load with window.LANKAGRID_API_BASE_URL if needed.
const API_BASE_URL = (
  window.LANKAGRID_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");
const AUTH_API_URL = API_BASE_URL + "/api/v1/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCakTBGeKbwDin92DaLZl-5Y8drePPhsgI",
  authDomain: "smart-electrical-grid-ee080.firebaseapp.com",
  projectId: "smart-electrical-grid-ee080",
  storageBucket: "smart-electrical-grid-ee080.firebasestorage.app",
  messagingSenderId: "241237031288",
  appId: "1:241237031288:web:3ea735e13521b923e2f08d",
  measurementId: "G-NVQZBYVB42",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export { onAuthStateChanged, signOut };

function friendlyMessage(code) {
  switch (code) {
    case "auth/email-already-in-use":
      return "An account with this email already exists.";
    case "auth/weak-password":
      return "That password is too weak. Use at least 8 characters with letters, numbers and symbols.";
    case "auth/invalid-email":
      return "Enter a valid email address.";
    case "auth/invalid-credential":
    case "auth/invalid-login-credentials":
    case "auth/wrong-password":
    case "auth/user-not-found":
      return "Incorrect email or password.";
    case "auth/user-disabled":
      return "This account has been disabled. Please contact your administrator.";
    case "auth/too-many-requests":
      return "Too many attempts. Please wait a few minutes and try again.";
    case "auth/network-request-failed":
      return "Network error. Check your connection and try again.";
    case "auth/popup-closed-by-user":
    case "auth/cancelled-popup-request":
      return "Google sign-in was cancelled.";
    case "auth/popup-blocked":
      return "Your browser blocked the sign-in popup. Allow popups for this site and try again.";
    case "auth/operation-not-allowed":
      return "This sign-in method is not enabled yet. Please contact your administrator.";
    case "auth/unauthorized-domain":
      return "This domain is not authorized for sign-in. Add it under Firebase Authentication authorized domains.";
    default:
      return "Something went wrong. Please try again.";
  }
}

const toFriendlyError = (error) => new Error(friendlyMessage(error && error.code));

async function requestAuthApi(endpoint, options = {}) {
  const headers = {};
  if (options.body) headers["Content-Type"] = "application/json";
  if (options.token) headers.Authorization = "Bearer " + options.token;

  let response;
  try {
    response = await fetch(AUTH_API_URL + endpoint, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch (error) {
    throw new Error(
      "Could not reach the LankaGrid API at " + API_BASE_URL +
      ". Make sure FastAPI is running and the frontend API URL is correct."
    );
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    let message = data.detail || data.message || "The API request failed.";
    if (Array.isArray(message)) {
      message = message.map((item) => item.msg || "Invalid input").join(" ");
    }
    if (response.status === 401 && String(message).toLowerCase().includes("profile")) {
      message = "No application profile was found for this account. Please register first.";
    }
    throw new Error(String(message));
  }
  return data;
}

async function validateBackendLogin(user) {
  try {
    const idToken = await user.getIdToken();
    return await requestAuthApi("/login", {
      method: "POST",
      body: { firebase_id_token: idToken },
    });
  } catch (error) {
    await signOut(auth).catch(() => {});
    throw error;
  }
}

/** Email/password sign-in, followed by PostgreSQL profile validation. */
export async function handleLogin(email, password, remember) {
  let user;
  try {
    await setPersistence(
      auth,
      remember ? browserLocalPersistence : browserSessionPersistence
    );
    ({ user } = await signInWithEmailAndPassword(auth, email, password));
  } catch (error) {
    throw toFriendlyError(error);
  }

  if (!user.emailVerified) {
    await signOut(auth).catch(() => {});
    throw new Error(
      "Please verify your email before signing in. Check your inbox and spam folder."
    );
  }

  await validateBackendLogin(user);
  return { redirectTo: AFTER_LOGIN_URL };
}

/**
 * Create the Firebase account, then create its PostgreSQL application profile.
 * Passwords remain exclusively in Firebase Authentication.
 */
export async function handleRegister({ name, email, password, nic, employeeId }) {
  let credential;
  try {
    credential = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(credential.user, { displayName: name });

    const idToken = await credential.user.getIdToken();
    await requestAuthApi("/register", {
      method: "POST",
      body: {
        email: credential.user.email,
        fullname: name,
        nic,
        employee_id: employeeId,
        firebase_id_token: idToken,
      },
    });

    await sendEmailVerification(credential.user);
    await signOut(auth);
    return {};
  } catch (error) {
    await signOut(auth).catch(() => {});
    if (error && error.code) throw toFriendlyError(error);
    throw error;
  }
}

/** Google sign-in is accepted only for accounts that already have a DB profile. */
export async function handleGoogle() {
  let user;
  try {
    ({ user } = await signInWithPopup(auth, new GoogleAuthProvider()));
  } catch (error) {
    throw toFriendlyError(error);
  }

  if (!user.emailVerified) {
    await signOut(auth).catch(() => {});
    throw new Error("Verify your email address before signing in.");
  }

  await validateBackendLogin(user);
  return { redirectTo: AFTER_LOGIN_URL };
}

/** Load the authoritative user profile from FastAPI/PostgreSQL. */
export async function getCurrentUserProfile(user) {
  const idToken = await user.getIdToken();
  return requestAuthApi("/me", { token: idToken });
}

/** Send a password-reset email without revealing whether the account exists. */
export async function handleForgotPassword(email) {
  try {
    await sendPasswordResetEmail(auth, email);
  } catch (error) {
    if (error && error.code === "auth/user-not-found") return {};
    throw toFriendlyError(error);
  }
  return {};
}

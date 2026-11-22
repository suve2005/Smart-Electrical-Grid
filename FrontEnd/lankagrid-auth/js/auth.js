/* ==========================================================================
   auth.js – Firebase authentication for LankaGrid
   --------------------------------------------------------------------------
   Exports used by the UI (login.js / register.js):
     handleLogin(email, password, remember)
     handleRegister({ name, email, password, role })
     handleGoogle()
     handleForgotPassword(email)
   Also exports `auth` and `db` so other pages (e.g. a dashboard guard) can
   import them from this one file.

   Contract used by login.js / register.js:
     - resolve  -> success (optionally { redirectTo: 'dashboard.html' })
     - throw    -> new Error('Friendly message to show the user')

   Security notes:
     - New profiles use only ALLOWED_ROLES; missing or invalid selections
       default to 'viewer'. Firestore rules enforce the same allowlist.
     - Roles selected by users should not grant privileges unless that
       self-assignment is intentional.
     - Raw Firebase error text is never shown; codes are mapped to friendly
       messages, and failed logins use one generic message.
     - Passwords are never logged or stored.
   ========================================================================== */

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
import {
  getFirestore,
  doc,
  getDoc,
  setDoc,
  serverTimestamp,
} from "https://www.gstatic.com/firebasejs/11.0.0/firebase-firestore.js";

/** Demo notices are off now that Firebase is connected. */
export const DEMO_MODE = false;

const ALLOWED_ROLES = ["grid-operator", "engineer", "analyst", "viewer"];

/**
 * Where to send users after a successful login.
 */
const AFTER_LOGIN_URL = "dashboard.html";

/* ----------------------------------------------------------- FIREBASE --- */
// The web apiKey is not a secret: access is controlled by your Firebase
// security rules and the authorized domains list, not by hiding this config.
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
export const db = getFirestore(app);
export { onAuthStateChanged, signOut };

/* ------------------------------------------------------------- HELPERS --- */

/** Map Firebase error codes to messages that are safe to show users. */
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
      return "Incorrect email or password."; // generic on purpose
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
      return "This domain is not authorized for sign-in. Add it under Firebase > Authentication > Settings > Authorized domains.";
    default:
      return "Something went wrong. Please try again.";
  }
}

const toFriendlyError = (err) => new Error(friendlyMessage(err && err.code));

/**
 * Create users/{uid} if it does not exist yet. Never throws: a missing profile
 * must not block registration or login (it is retried on the next login).
 * Saves only an allowed role; missing or invalid selections default to viewer.
 */
async function ensureUserProfile(user, extra = {}) {
  try {
    const ref = doc(db, "users", user.uid);
    const snap = await getDoc(ref);
    if (snap.exists()) return;

    const role = ALLOWED_ROLES.includes(extra.role)
      ? extra.role
      : "viewer";

    await setDoc(ref, {
      name: extra.name || user.displayName || "",
      email: user.email, // use Firebase's normalised (lowercase) email
      role,
      createdAt: serverTimestamp(),
    });
  } catch (err) {
    console.warn("User profile was not saved:", (err && err.code) || "unknown error");
  }
}

/* ---------------------------------------------------------------- LOGIN --- */
/** Sign in with email + password. Blocks accounts whose email is unverified. */
export async function handleLogin(email, password, remember) {
  let user;
  try {
    // "Remember me" -> stay signed in across browser restarts; otherwise
    // only for this tab/session.
    await setPersistence(auth, remember ? browserLocalPersistence : browserSessionPersistence);
    ({ user } = await signInWithEmailAndPassword(auth, email, password));
  } catch (err) {
    throw toFriendlyError(err);
  }

  if (!user.emailVerified) {
    await signOut(auth).catch(() => {});
    throw new Error(
      "Please verify your email before signing in. Check your inbox (and spam folder) for the verification link."
    );
  }

  await ensureUserProfile(user);
  return { redirectTo: AFTER_LOGIN_URL };
}

/* ------------------------------------------------------------- REGISTER --- */
/**
 * Create an account, send the verification email, then sign out so the user
 * must verify before their first login.
 * @param {{name:string,email:string,password:string,role:string}} data
 */
export async function handleRegister({ name, email, password, role }) {
  let cred;
  try {
    cred = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(cred.user, { displayName: name });
    await sendEmailVerification(cred.user);
  } catch (err) {
    throw toFriendlyError(err);
  }

  await ensureUserProfile(cred.user, { name, role });
  await signOut(auth).catch(() => {});
  return {};
}

/* --------------------------------------------------------------- GOOGLE --- */
/** Continue with Google (accounts arrive already verified). */
export async function handleGoogle() {
  let user;
  try {
    ({ user } = await signInWithPopup(auth, new GoogleAuthProvider()));
  } catch (err) {
    throw toFriendlyError(err);
  }

  await ensureUserProfile(user);
  return { redirectTo: AFTER_LOGIN_URL };
}

/* ------------------------------------------------------ FORGOT PASSWORD --- */
/** Send a password-reset email without revealing whether the account exists. */
export async function handleForgotPassword(email) {
  try {
    await sendPasswordResetEmail(auth, email);
  } catch (err) {
    if (err && err.code === "auth/user-not-found") return {}; // don't reveal
    throw toFriendlyError(err);
  }
  return {};
}
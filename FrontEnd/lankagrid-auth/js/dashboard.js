import { doc, getDoc } from 'https://www.gstatic.com/firebasejs/11.0.0/firebase-firestore.js';
import { auth, db, onAuthStateChanged, signOut } from './auth.js';

const nameEl = document.getElementById('user-name');
const emailEl = document.getElementById('user-email');
const roleEl = document.getElementById('user-role');
const alertEl = document.getElementById('dashboard-alert');
const signOutButton = document.getElementById('signout-btn');

function showError(message, error) {
  alertEl.textContent = message;
  alertEl.hidden = false;
  if (error) console.error(message, error);
}

async function loadProfile(user) {
  try {
    const profileSnapshot = await getDoc(doc(db, 'users', user.uid));
    if (!profileSnapshot.exists()) {
      nameEl.textContent = user.displayName || '—';
      emailEl.textContent = user.email || '—';
      roleEl.textContent = 'Unavailable';
      showError('Your profile could not be found. Please contact your administrator.');
      return;
    }

    const profile = profileSnapshot.data();
    nameEl.textContent =
      typeof profile.name === 'string' && profile.name.trim()
        ? profile.name
        : user.displayName || '—';
    emailEl.textContent =
      typeof profile.email === 'string' && profile.email
        ? profile.email
        : user.email || '—';
    roleEl.textContent =
      typeof profile.role === 'string' && profile.role
        ? profile.role
        : 'Unavailable';

    if (roleEl.textContent === 'Unavailable') {
      showError('Your profile does not include a role. Please contact your administrator.');
    }
  } catch (error) {
    nameEl.textContent = user.displayName || '—';
    emailEl.textContent = user.email || '—';
    roleEl.textContent = 'Unavailable';
    showError('We could not load your profile. Please refresh and try again.', error);
  }
}

onAuthStateChanged(auth, (user) => {
  if (!user || !user.emailVerified) return;

  nameEl.textContent = user.displayName || '—';
  emailEl.textContent = user.email || '—';
  roleEl.textContent = 'Loading…';
  loadProfile(user);
});

signOutButton.addEventListener('click', async () => {
  signOutButton.disabled = true;
  signOutButton.setAttribute('aria-busy', 'true');

  try {
    await signOut(auth);
    window.location.replace('index.html');
  } catch (error) {
    showError('We could not sign you out. Please try again.', error);
    signOutButton.disabled = false;
    signOutButton.removeAttribute('aria-busy');
  }
});

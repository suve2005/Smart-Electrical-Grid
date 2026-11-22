import { auth, onAuthStateChanged } from './auth.js';

const dashboard = document.getElementById('dashboard-content');

onAuthStateChanged(
  auth,
  (user) => {
    if (!user || !user.emailVerified) {
      window.location.replace('index.html');
      return;
    }

    dashboard.hidden = false;
  },
  () => {
    window.location.replace('index.html');
  }
);

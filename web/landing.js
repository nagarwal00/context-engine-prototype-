(() => {
  const matrix = document.querySelector('.code-matrix');
  const menuButton = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  const year = document.getElementById('footer-year');
  if (year) year.textContent = String(new Date().getFullYear());

  if (matrix) {
    const alphabet = '01#{}[]<>/;:abcdefXYZ$%&*+-=~';
    let seed = 72819;
    const random = () => {
      seed = (seed * 16807) % 2147483647;
      return seed / 2147483647;
    };
    const drawMatrix = () => {
      const rows = Math.ceil(window.innerHeight / 21) + 2;
      const columns = Math.ceil(window.innerWidth / 8) + 16;
      matrix.replaceChildren();
      for (let row = 0; row < rows; row++) {
        let line = '';
        for (let col = 0; col < columns; col++) {
          const chance = random();
          line += chance < .13 ? ' ' : alphabet[Math.floor(random() * alphabet.length)];
        }
        const element = document.createElement('span');
        element.className = 'code-row';
        element.textContent = line;
        matrix.append(element);
      }
    };
    drawMatrix();
    let resizeTimer;
    window.addEventListener('resize', () => {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(drawMatrix, 120);
    }, { passive: true });
  }

  if (menuButton && nav) {
    menuButton.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      menuButton.setAttribute('aria-expanded', String(open));
      menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
      nav.classList.remove('open');
      menuButton.setAttribute('aria-expanded', 'false');
      menuButton.setAttribute('aria-label', 'Open navigation');
    }));
  }

  // Account Sign-In / Register Modal Logic
  const loginModal = document.getElementById('login-modal');
  const getStartedBtn = document.getElementById('header-get-started');
  const modalCloseBtn = document.getElementById('modal-login-close');
  const authTabs = document.querySelectorAll('.auth-tab');
  const authForm = document.getElementById('landing-auth-form');
  const authSubmit = document.getElementById('landing-auth-submit');
  const authMsg = document.getElementById('landing-auth-msg');

  const authStatusBadge = document.getElementById('auth-status-badge');
  const authStatusText = document.getElementById('auth-status-text');
  const logoutBtn = document.getElementById('header-logout-btn');

  let isAuthenticated = false;
  let currentUser = null;
  let currentAuthMode = 'signin';
  let pendingRedirectUrl = 'dashboard.html';

  const updateAuthUI = (auth, user) => {
    isAuthenticated = Boolean(auth);
    currentUser = user || null;

    if (authStatusBadge) {
      if (isAuthenticated && currentUser && currentUser.login) {
        authStatusBadge.className = 'auth-status-badge status-authenticated';
        authStatusBadge.title = `Signed in as ${currentUser.login}`;
        const avatarHtml = currentUser.avatar_url
          ? `<img class="auth-avatar" src="${currentUser.avatar_url}" alt="" />`
          : '';
        authStatusBadge.innerHTML = `<span class="auth-status-dot" aria-hidden="true"></span>${avatarHtml}<span class="auth-status-text">${currentUser.login}</span>`;
      } else {
        authStatusBadge.className = 'auth-status-badge status-unauthenticated';
        authStatusBadge.title = 'Not signed in';
        authStatusBadge.innerHTML = `<span class="auth-status-dot" aria-hidden="true"></span><span class="auth-status-text">Not logged in</span>`;
      }
    }

    if (logoutBtn) {
      if (isAuthenticated) {
        logoutBtn.classList.remove('button-logout-disabled');
        logoutBtn.removeAttribute('disabled');
        logoutBtn.title = 'Log out of Context Engine';
      } else {
        logoutBtn.classList.add('button-logout-disabled');
        logoutBtn.title = 'You are not logged in';
      }
    }

    if (getStartedBtn) {
      if (isAuthenticated) {
        getStartedBtn.innerHTML = 'Workspace <span aria-hidden="true">→</span>';
        getStartedBtn.setAttribute('href', 'dashboard.html');
      } else {
        getStartedBtn.innerHTML = 'Get started <span aria-hidden="true">→</span>';
        getStartedBtn.setAttribute('href', 'login.html');
      }
    }
  };

  const checkAuth = async () => {
    try {
      const res = await fetch('/auth/me');
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          updateAuthUI(true, data.user);
          return;
        }
      }
    } catch (e) {}

    try {
      const res = await fetch('/api/me');
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success' && data.login) {
          updateAuthUI(true, { login: data.login, avatar_url: data.avatar_url });
          return;
        }
      }
    } catch (e) {}

    updateAuthUI(false, null);
  };

  checkAuth();

  if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      if (!isAuthenticated) {
        openLoginModal('dashboard.html');
        return;
      }

      logoutBtn.disabled = true;
      logoutBtn.style.opacity = '0.6';
      logoutBtn.innerHTML = '<span>Logging out...</span>';

      try {
        await fetch('/auth/logout', { method: 'POST' });
      } catch (err) {}

      updateAuthUI(false, null);
      logoutBtn.disabled = false;
      logoutBtn.style.opacity = '';
      logoutBtn.innerHTML = `
        <svg class="logout-icon" viewBox="0 0 16 16" fill="none" width="13" height="13" aria-hidden="true">
          <path d="M6 2H3.5A1.5 1.5 0 0 0 2 3.5v9A1.5 1.5 0 0 0 3.5 14H6M10.5 11.5 14 8m0 0-3.5-3.5M14 8H5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Logout</span>
      `;

      if (window.location.search.includes('logged_out')) {
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    });
  }

  const openLoginModal = (target) => {
    if (typeof target === 'string') {
      pendingRedirectUrl = target;
    } else if (target && target.currentTarget && target.currentTarget.getAttribute('href')) {
      pendingRedirectUrl = target.currentTarget.getAttribute('href');
    } else {
      pendingRedirectUrl = 'dashboard.html';
    }

    const ghLink = loginModal ? loginModal.querySelector('.provider-login-link') : null;
    if (ghLink) {
      const nextParam = pendingRedirectUrl.startsWith('/') ? pendingRedirectUrl : '/' + pendingRedirectUrl;
      ghLink.href = '/auth/github/login?next=' + encodeURIComponent(nextParam);
    }

    const demoLink = loginModal ? loginModal.querySelector('.demo-action-btn') : null;
    if (demoLink) {
      const nextParam = pendingRedirectUrl.startsWith('/') ? pendingRedirectUrl : '/' + pendingRedirectUrl;
      demoLink.href = '/auth/demo/login?next=' + encodeURIComponent(nextParam);
    }

    if (loginModal) {
      loginModal.classList.remove('hidden');
      const input = loginModal.querySelector('input');
      if (input) input.focus();
    }
  };

  const closeLoginModal = () => {
    if (loginModal) {
      loginModal.classList.add('hidden');
      if (authMsg) {
        authMsg.className = 'auth-msg hidden';
        authMsg.textContent = '';
      }
    }
  };

  if (getStartedBtn) {
    getStartedBtn.addEventListener('click', (e) => {
      if (!isAuthenticated) {
        e.preventDefault();
        openLoginModal('dashboard.html');
      }
    });
  }

  // Intercept all feature and workspace links if not authenticated
  document.querySelectorAll('a[href^="dashboard.html"]').forEach(link => {
    link.addEventListener('click', (e) => {
      if (!isAuthenticated) {
        e.preventDefault();
        openLoginModal(link.getAttribute('href'));
      }
    });
  });

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closeLoginModal);
  }

  if (loginModal) {
    loginModal.addEventListener('click', (e) => {
      if (e.target === loginModal) {
        closeLoginModal();
      }
    });
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !loginModal.classList.contains('hidden')) {
        closeLoginModal();
      }
    });
  }

  authTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      authTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentAuthMode = tab.dataset.tab;
      if (authSubmit) {
        authSubmit.textContent = currentAuthMode === 'register' ? 'Create Account & Sign In' : 'Sign in';
      }
      if (authMsg) {
        authMsg.className = 'auth-msg hidden';
        authMsg.textContent = '';
      }
    });
  });

  if (authForm) {
    authForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const usernameInput = document.getElementById('landing-username');
      const passwordInput = document.getElementById('landing-password');
      const username = usernameInput ? usernameInput.value.trim() : '';
      const password = passwordInput ? passwordInput.value : '';

      if (!username) {
        if (authMsg) {
          authMsg.className = 'auth-msg error';
          authMsg.textContent = 'Please enter a username or email.';
        }
        return;
      }

      if (authSubmit) {
        authSubmit.disabled = true;
        authSubmit.textContent = 'Please wait...';
      }

      try {
        const endpoint = currentAuthMode === 'register' ? '/auth/register' : '/auth/login';
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: username,
            password: password,
            action: currentAuthMode,
            next: pendingRedirectUrl.startsWith('/') ? pendingRedirectUrl : '/' + pendingRedirectUrl
          })
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
          if (authMsg) {
            authMsg.className = 'auth-msg success';
            authMsg.textContent = data.message || 'Success! Redirecting to workspace...';
          }
          if (data.user) {
            updateAuthUI(true, data.user);
          }
          window.setTimeout(() => {
            window.location.href = data.redirect || pendingRedirectUrl || 'dashboard.html';
          }, 400);
        } else {
          if (authMsg) {
            authMsg.className = 'auth-msg error';
            authMsg.textContent = data.message || 'Authentication failed. Please try again.';
          }
          if (authSubmit) {
            authSubmit.disabled = false;
            authSubmit.textContent = currentAuthMode === 'register' ? 'Create Account & Sign In' : 'Sign in';
          }
        }
      } catch (err) {
        if (authMsg) {
          authMsg.className = 'auth-msg error';
          authMsg.textContent = 'Network error. Please try again or use GitHub sign-in.';
        }
        if (authSubmit) {
          authSubmit.disabled = false;
          authSubmit.textContent = currentAuthMode === 'register' ? 'Create Account & Sign In' : 'Sign in';
        }
      }
    });
  }
})();

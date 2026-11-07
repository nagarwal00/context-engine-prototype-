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

  let currentAuthMode = 'signin';

  const openLoginModal = (e) => {
    if (e) e.preventDefault();
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
    getStartedBtn.addEventListener('click', openLoginModal);
  }

  let isAuthenticated = false;
  fetch('/api/me')
    .then(r => {
      if (r.ok) isAuthenticated = true;
    })
    .catch(() => {});

  // Intercept dashboard links if not authenticated
  document.querySelectorAll('a[href="dashboard.html"]').forEach(link => {
    link.addEventListener('click', (e) => {
      if (!isAuthenticated) {
        e.preventDefault();
        openLoginModal(e);
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
            action: currentAuthMode
          })
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
          if (authMsg) {
            authMsg.className = 'auth-msg success';
            authMsg.textContent = data.message || 'Success! Redirecting to workspace...';
          }
          window.setTimeout(() => {
            window.location.href = data.redirect || 'dashboard.html';
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

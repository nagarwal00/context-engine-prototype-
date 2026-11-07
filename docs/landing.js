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
})();

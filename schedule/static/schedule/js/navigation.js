(() => {
  const button = document.getElementById('menu-toggle');
  const nav = document.getElementById('site-nav');
  if (!button || !nav) return;

  const mobile = window.matchMedia('(max-width: 480px)');

  function closeMenu(returnFocus = false) {
    nav.classList.remove('is-open');
    document.body.classList.remove('menu-open');
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-label', '開啟主選單');
    if (returnFocus) button.focus();
  }

  function openMenu() {
    nav.classList.add('is-open');
    document.body.classList.add('menu-open');
    button.setAttribute('aria-expanded', 'true');
    button.setAttribute('aria-label', '關閉主選單');
    const firstItem = nav.querySelector('a, summary');
    if (firstItem) firstItem.focus();
  }

  button.addEventListener('click', () => {
    const isOpen = button.getAttribute('aria-expanded') === 'true';
    if (isOpen) closeMenu();
    else openMenu();
  });

  nav.addEventListener('click', (event) => {
    if (event.target === nav) closeMenu(true);
    else if (event.target.closest('a')) closeMenu();
  });

  document.addEventListener('click', (event) => {
    if (mobile.matches && button.getAttribute('aria-expanded') === 'true'
      && !nav.contains(event.target) && !button.contains(event.target)) closeMenu();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') {
      closeMenu(true);
    }
  });

  mobile.addEventListener('change', () => closeMenu());
})();

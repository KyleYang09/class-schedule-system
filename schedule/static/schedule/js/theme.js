(() => {
  const KEY = 'schedule.theme';
  const root = document.documentElement;
  const button = document.getElementById('theme-toggle');
  if (!button) return;
  let transitionTimer;

  const sync = () => button.setAttribute('aria-pressed', String(root.dataset.theme === 'dark'));

  button.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    window.clearTimeout(transitionTimer);
    root.classList.add('theme-switching');
    root.dataset.theme = next;
    transitionTimer = window.setTimeout(() => root.classList.remove('theme-switching'), 360);
    try {
      localStorage.setItem(KEY, next);
    } catch (e) {}
    sync();
  });

  sync();
})();

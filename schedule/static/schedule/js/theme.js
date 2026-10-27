(() => {
  const KEY = 'schedule.theme';
  const root = document.documentElement;
  const button = document.getElementById('theme-toggle');
  if (!button) return;

  const sync = () => button.setAttribute('aria-pressed', String(root.dataset.theme === 'dark'));

  button.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.classList.add('theme-switching');
    root.dataset.theme = next;
    requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove('theme-switching')));
    try {
      localStorage.setItem(KEY, next);
    } catch (e) {}
    sync();
  });

  sync();
})();

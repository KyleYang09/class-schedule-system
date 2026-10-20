(function () {
  const input = document.querySelector('[data-filter-target]');
  if (!input) return;
  const list = document.querySelector(input.dataset.filterTarget);
  const none = document.getElementById('picker-none');
  const items = Array.from(list.querySelectorAll('li'));

  input.addEventListener('input', () => {
    const keyword = input.value.trim().toLowerCase();
    let visible = 0;
    items.forEach((item) => {
      const match = item.textContent.toLowerCase().includes(keyword);
      item.hidden = !match;
      if (match) visible += 1;
    });
    none.hidden = visible > 0;
  });
})();

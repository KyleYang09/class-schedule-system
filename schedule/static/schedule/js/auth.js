(function () {
  var forms = document.querySelectorAll('form[data-pending]');

  function reset() {
    forms.forEach(function (form) {
      var button = form.querySelector('button[type="submit"]');
      if (button && button.dataset.label) {
        button.textContent = button.dataset.label;
        button.disabled = false;
        button.removeAttribute('aria-busy');
      }
    });
  }

  forms.forEach(function (form) {
    form.addEventListener('submit', function (event) {
      var button = form.querySelector('button[type="submit"]');
      if (!button || button.disabled) {
        event.preventDefault();
        return;
      }
      button.dataset.label = button.textContent;
      button.textContent = form.dataset.pending;
      button.setAttribute('aria-busy', 'true');
      setTimeout(function () { button.disabled = true; }, 0);
    });
  });

  window.addEventListener('pageshow', function (event) {
    if (event.persisted) reset();
  });
})();

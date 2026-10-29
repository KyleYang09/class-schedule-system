(function () {
  var forms = document.querySelectorAll('form[data-pending]');

  document.querySelectorAll('.auth-form').forEach(function (form) {
    form.querySelectorAll('.auth-form__row').forEach(function (row, rowIndex) {
      var field = row.querySelector('input:not([type="hidden"]), select, textarea');
      var errors = row.querySelectorAll('.auth-form__error');
      if (!field || !errors.length) return;

      field.setAttribute('aria-invalid', 'true');
      var describedBy = (field.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
      errors.forEach(function (error, errorIndex) {
        if (!error.id) error.id = 'field-error-' + rowIndex + '-' + errorIndex;
        describedBy.push(error.id);
      });
      field.setAttribute('aria-describedby', Array.from(new Set(describedBy)).join(' '));
    });
  });

  var errorTarget = document.querySelector('.auth-form__error-summary, .auth-form__alert[role="alert"]');
  if (errorTarget) errorTarget.focus();

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

(function () {
  var form = document.querySelector('form[data-pending]');
  if (!form) return;

  var roles = form.querySelectorAll('input[name="role"]');
  var sections = form.querySelectorAll('[data-role-section]');
  var teacherSelect = form.querySelector('select[name="teacher_choice"]');
  var newTeacher = form.querySelector('[data-new-teacher]');

  function checkedRole() {
    var checked = form.querySelector('input[name="role"]:checked');
    return checked ? checked.value : '';
  }

  function sync() {
    var role = checkedRole();
    sections.forEach(function (section) {
      section.hidden = section.dataset.roleSection !== role;
    });
    newTeacher.hidden = !(role === 'teacher' && teacherSelect.value === 'new');
  }

  roles.forEach(function (radio) { radio.addEventListener('change', sync); });
  teacherSelect.addEventListener('change', sync);
  sync();
})();

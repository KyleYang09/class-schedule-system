(function () {
  const STORAGE_KEY = 'schedule.my.courses';
  const TINT_COUNT = 4;
  const data = JSON.parse(document.getElementById('timetable-data').textContent);
  const courseById = new Map(data.courses.map((course) => [course.id, course]));
  const periodById = new Map(data.periods.map((period) => [period.id, period]));
  const dayLabel = new Map(data.weekdays.map((day) => [day.number, day.label]));

  const classSelect = document.getElementById('my-class');
  const courseList = document.getElementById('my-courses');
  const summary = document.getElementById('my-summary');
  const conflicts = document.getElementById('my-conflicts');
  const emptyState = document.getElementById('my-empty');
  const gridHost = document.getElementById('my-grid');
  const selectedBox = document.getElementById('my-selected');
  const selectedList = document.getElementById('my-selected-list');
  const clearButton = document.getElementById('my-clear');

  function load() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      return new Set(saved.filter((id) => courseById.has(id)));
    } catch (error) {
      return new Set();
    }
  }

  let selected = load();

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(selected)));
    } catch (error) {
      /* storage unavailable: selection lasts for this visit only */
    }
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function slotText(course) {
    return course.slots
      .slice()
      .sort((a, b) => a.day - b.day || a.period - b.period)
      .map((slot) => `${dayLabel.get(slot.day)} 第${periodById.get(slot.period).code}節`)
      .join('、');
  }

  function toggle(id, on) {
    if (on) selected.add(id);
    else selected.delete(id);
    save();
    render();
  }

  function renderClassOptions() {
    data.classes.forEach((item) => {
      const option = el('option', '', item.name);
      option.value = item.id;
      classSelect.append(option);
    });
    const lastClass = selected.size ? courseById.get(Array.from(selected).pop()).classId : null;
    if (lastClass) classSelect.value = lastClass;
  }

  function renderCourseList() {
    courseList.replaceChildren();
    const classId = Number(classSelect.value);
    data.courses.filter((course) => course.classId === classId).forEach((course) => {
      const item = el('li');
      const label = el('label', 'course-option');
      const box = el('input');
      box.type = 'checkbox';
      box.checked = selected.has(course.id);
      box.addEventListener('change', () => toggle(course.id, box.checked));
      const text = el('span', 'course-option__text');
      text.append(el('strong', '', course.name), el('small', '', `${course.teacher}・${slotText(course) || '未排時段'}`));
      label.append(box, text);
      item.append(label);
      courseList.append(item);
    });
  }

  function buildCells() {
    const cells = new Map();
    selected.forEach((id) => {
      const course = courseById.get(id);
      course.slots.forEach((slot) => {
        const key = `${slot.day}-${slot.period}`;
        if (!cells.has(key)) cells.set(key, []);
        cells.get(key).push({ course, slot });
      });
    });
    return cells;
  }

  function renderGrid(cells) {
    const days = data.weekdays.filter((day) => day.number <= 5 || Array.from(cells.keys()).some((key) => key.startsWith(`${day.number}-`)));
    const wrap = el('div', 'grid-wrap');
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label', '我的課表');
    wrap.tabIndex = 0;
    const table = el('table', 'grid');
    const head = el('tr');
    head.append(Object.assign(el('th', 'grid__corner', '節次'), { scope: 'col' }));
    days.forEach((day) => head.append(Object.assign(el('th', '', day.label), { scope: 'col' })));
    const thead = el('thead');
    thead.append(head);
    table.append(thead);
    const body = el('tbody');
    data.periods.forEach((period) => {
      const row = el('tr');
      const header = Object.assign(el('th', 'grid__period'), { scope: 'row' });
      header.append(el('b', '', period.code), el('small', '', `${period.start}–${period.end}`));
      row.append(header);
      days.forEach((day) => {
        const cell = el('td');
        const entries = cells.get(`${day.number}-${period.id}`) || [];
        entries.forEach(({ course, slot }) => {
          const lesson = el('div', `lesson tint-${course.id % TINT_COUNT}${entries.length > 1 ? ' lesson--conflict' : ''}`);
          if (entries.length > 1) lesson.append(el('em', 'lesson__flag', '衝突'));
          lesson.append(el('strong', '', course.name), el('span', '', `${course.className}・${course.teacher}`), el('span', '', slot.room));
          cell.append(lesson);
        });
        row.append(cell);
      });
      body.append(row);
    });
    table.append(body);
    wrap.append(table);
    gridHost.replaceChildren(wrap);
  }

  function renderSelected() {
    selectedList.replaceChildren();
    Array.from(selected).map((id) => courseById.get(id)).forEach((course) => {
      const item = el('li');
      const text = el('span');
      text.append(el('strong', '', course.name), el('small', '', `${course.className}・${course.teacher}・${slotText(course)}`));
      const remove = el('button', 'btn btn--quiet', '移除');
      remove.type = 'button';
      remove.setAttribute('aria-label', `移除 ${course.name}`);
      remove.addEventListener('click', () => toggle(course.id, false));
      item.append(text, remove);
      selectedList.append(item);
    });
  }

  function render() {
    renderCourseList();
    const cells = buildCells();
    const clashes = Array.from(cells.entries()).filter(([, entries]) => entries.length > 1);
    const hasSelection = selected.size > 0;

    emptyState.hidden = hasSelection;
    gridHost.hidden = !hasSelection;
    selectedBox.hidden = !hasSelection;
    summary.textContent = hasSelection ? `已加入 ${selected.size} 門課` : '';

    conflicts.hidden = clashes.length === 0;
    if (clashes.length) {
      const lines = clashes.map(([key, entries]) => {
        const [day, period] = key.split('-').map(Number);
        return `${dayLabel.get(day)} 第${periodById.get(period).code}節:${entries.map((entry) => entry.course.name).join('、')}`;
      });
      conflicts.textContent = `有 ${clashes.length} 個時段衝突。${lines.join(';')}`;
    }

    if (hasSelection) {
      renderGrid(cells);
      renderSelected();
    } else {
      gridHost.replaceChildren();
    }
  }

  clearButton.addEventListener('click', () => {
    if (window.confirm('確定要移除所有已加入的課程嗎?')) {
      selected = new Set();
      save();
      render();
    }
  });
  classSelect.addEventListener('change', renderCourseList);

  renderClassOptions();
  render();
})();

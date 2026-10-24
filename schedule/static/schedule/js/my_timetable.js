(function () {
  const STORAGE_KEY = 'schedule.my.courses';
  const FILL_COUNT = 4;
  const TILE_HEIGHT = 100;
  const TILE_GAP = 8;
  const TILE_PADDING = 28;
  const CHAR_HEIGHT = 22;
  const SMALL_CHAR_HEIGHT = 16;
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

  function textLength(text, unit) {
    return Array.from(text).reduce((sum, char) => sum + unit * (char.charCodeAt(0) < 128 ? 0.55 : 1), 0);
  }

  function fitsVertically(name, smallTexts, span) {
    if (span < 2) return false;
    const height = span * TILE_HEIGHT + (span - 1) * TILE_GAP - TILE_PADDING;
    return textLength(name, CHAR_HEIGHT) <= height && smallTexts.every((text) => text.length * SMALL_CHAR_HEIGHT <= height);
  }

  function renderGrid(cells) {
    const days = data.weekdays;
    const now = new Date();
    const today = now.getDay() === 0 ? 7 : now.getDay();
    const clock = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    const board = el('div', 'board');
    const wrap = el('div', 'sheet');
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label', '我的課表');
    wrap.tabIndex = 0;
    const table = el('table', 'grid');
    const thead = el('thead');
    const head = el('tr');
    const corner = Object.assign(el('th', 'grid__corner'), { scope: 'col' });
    corner.append(el('span', 'sr-only', '節次'));
    head.append(corner);
    days.forEach((day) => {
      const classes = ['tile'];
      if (day.number > 5) classes.push('is-weekend');
      if (day.number === today) classes.push('is-today');
      const th = Object.assign(el('th', classes.join(' '), day.label), { scope: 'col' });
      if (day.number === today) th.append(el('small', '', '今天'));
      head.append(th);
    });
    thead.append(head);
    table.append(thead);

    const body = el('tbody');
    const skipped = new Set();
    const entriesAt = (day, index) => (data.periods[index] ? cells.get(`${day}-${data.periods[index].id}`) || [] : []);

    data.periods.forEach((period, index) => {
      if (period.breakLabel) {
        const gap = el('tr', 'grid__break');
        gap.append(Object.assign(el('th', '', period.breakLabel), { scope: 'row' }));
        const note = el('td');
        note.append(el('span', '', period.breakTime));
        note.colSpan = days.length;
        gap.append(note);
        body.append(gap);
      }
      const row = el('tr');
      const isNow = period.start <= clock && clock <= period.end;
      const header = Object.assign(el('th', `tile grid__period${isNow ? ' is-now' : ''}`), { scope: 'row' });
      const time = el('small');
      time.append(period.start, document.createElement('br'), period.end);
      header.append(el('b', '', period.code), time);
      if (isNow) header.append(el('em', '', '現在'));
      row.append(header);

      days.forEach((day) => {
        if (skipped.has(`${day.number}-${index}`)) return;
        const entries = entriesAt(day.number, index);
        const cell = el('td', 'tile');
        if (entries.length === 0) {
          cell.classList.add('tile--empty');
          if (day.number > 5) cell.classList.add('tile--weekend');
          if (day.number === today) cell.classList.add('tile--today');
        } else if (entries.length === 1) {
          const { course, slot } = entries[0];
          let span = 1;
          while (
            !data.periods[index + span]?.breakLabel &&
            entriesAt(day.number, index + span).length === 1 &&
            entriesAt(day.number, index + span)[0].course.id === course.id &&
            entriesAt(day.number, index + span)[0].slot.room === slot.room
          ) {
            skipped.add(`${day.number}-${index + span}`);
            span += 1;
          }
          if (span > 1) cell.rowSpan = span;
          const details = [`${course.className}・${course.teacher}`];
          cell.classList.add(`fill-${course.id % FILL_COUNT}`);
          if (fitsVertically(course.name, [...details, slot.room], span)) cell.classList.add('is-vertical');
          const inner = el('div', 'tile__body');
          inner.append(el('strong', '', course.name), ...details.map((text) => el('span', '', text)), el('span', '', slot.room));
          cell.append(inner);
        } else {
          cell.classList.add('is-conflict');
          const inner = el('div', 'tile__body');
          inner.append(el('em', 'conflict-flag', '衝突'));
          entries.forEach(({ course }) => inner.append(el('strong', '', course.name)));
          cell.append(inner);
        }
        row.append(cell);
      });
      body.append(row);
    });
    table.append(body);
    wrap.append(table);
    board.append(wrap);
    gridHost.replaceChildren(board);
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

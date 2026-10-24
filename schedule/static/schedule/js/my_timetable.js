(function () {
  const STORAGE_KEY = 'schedule.my.courses';
  const FILL_COUNT = 4;
  const TILE_GAP = 8;
  const TILE_PADDING = 28;
  const CHAR_HEIGHT = 22;
  const SMALL_CHAR_HEIGHT = 16;
  const FULL = { tileHeight: 100, compact: false };
  const COMPACT = { tileHeight: 64, compact: true };

  const data = JSON.parse(document.getElementById('timetable-data').textContent);
  const courseById = new Map(data.courses.map((course) => [course.id, course]));
  const periodById = new Map(data.periods.map((period) => [period.id, period]));
  const dayLabel = new Map(data.weekdays.map((day) => [day.number, day.label]));

  const $ = (id) => document.getElementById(id);
  const main = {
    summary: $('my-summary'),
    conflicts: $('my-conflicts'),
    empty: $('my-empty'),
    grid: $('my-grid'),
  };
  const editor = {
    dialog: $('editor'),
    openButton: $('editor-open'),
    classSelect: $('my-class'),
    courseList: $('my-courses'),
    draftList: $('draft-list'),
    draftEmpty: $('draft-empty'),
    draftCount: $('draft-count'),
    clearButton: $('draft-clear'),
    conflicts: $('draft-conflicts'),
    previewEmpty: $('preview-empty'),
    previewGrid: $('preview-grid'),
    diff: $('draft-diff'),
    saveButton: $('editor-save'),
    cancelButton: $('editor-cancel'),
    tabs: ['pick', 'selected', 'preview'].map((name) => ({
      name,
      tab: $(`tab-${name}`),
      panel: $(`panel-${name}`),
    })),
  };

  let selected = load();
  let draft = new Set();
  let activeTab = 'pick';
  const courseRefs = new Map();
  const wide = window.matchMedia('(min-width: 900px)');

  function load() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      return new Set(saved.filter((id) => courseById.has(id)));
    } catch (error) {
      return new Set();
    }
  }

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

  function buildCells(ids) {
    const cells = new Map();
    ids.forEach((id) => {
      const course = courseById.get(id);
      course.slots.forEach((slot) => {
        const key = `${slot.day}-${slot.period}`;
        if (!cells.has(key)) cells.set(key, []);
        cells.get(key).push({ course, slot });
      });
    });
    return cells;
  }

  function findClashes(cells) {
    return Array.from(cells.entries())
      .filter(([, entries]) => entries.length > 1)
      .map(([key, entries]) => {
        const [day, period] = key.split('-').map(Number);
        return `${dayLabel.get(day)} 第${periodById.get(period).code}節:${entries.map((entry) => entry.course.name).join('、')}`;
      });
  }

  function textLength(text, unit) {
    return Array.from(text).reduce((sum, char) => sum + unit * (char.charCodeAt(0) < 128 ? 0.55 : 1), 0);
  }

  function fitsVertically(name, smallTexts, span, tileHeight) {
    if (span < 2) return false;
    const height = span * tileHeight + (span - 1) * TILE_GAP - TILE_PADDING;
    return textLength(name, CHAR_HEIGHT) <= height && smallTexts.every((text) => text.length * SMALL_CHAR_HEIGHT <= height);
  }

  function renderGrid(host, cells, options) {
    const now = new Date();
    const today = now.getDay() === 0 ? 7 : now.getDay();
    const clock = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    const board = el('div', 'board');
    const wrap = el('div', 'sheet');
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label', options.compact ? '課表預覽' : '我的課表');
    wrap.tabIndex = 0;
    const table = el('table', options.compact ? 'grid grid--compact' : 'grid');

    const thead = el('thead');
    const head = el('tr');
    const corner = Object.assign(el('th', 'grid__corner'), { scope: 'col' });
    corner.append(el('span', 'sr-only', '節次'));
    head.append(corner);
    data.weekdays.forEach((day) => {
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
        note.colSpan = data.weekdays.length;
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

      data.weekdays.forEach((day) => {
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
          const detail = `${course.className}・${course.teacher}`;
          cell.classList.add(`fill-${course.id % FILL_COUNT}`);
          if (fitsVertically(course.name, options.compact ? [slot.room] : [detail, slot.room], span, options.tileHeight)) cell.classList.add('is-vertical');
          const inner = el('div', 'tile__body');
          inner.append(el('strong', '', course.name), el('span', 'tile__detail', detail), el('span', '', slot.room));
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
    host.replaceChildren(board);
  }

  /* ---------- Main page ---------- */

  function renderMain() {
    const cells = buildCells(selected);
    const clashes = findClashes(cells);
    const hasSelection = selected.size > 0;

    main.summary.textContent = hasSelection ? `已加入 ${selected.size} 門課` : '';
    main.empty.hidden = hasSelection;
    main.grid.hidden = !hasSelection;
    main.conflicts.hidden = clashes.length === 0;
    if (clashes.length) main.conflicts.textContent = `有 ${clashes.length} 個時段衝突。${clashes.join(';')}`;

    if (hasSelection) renderGrid(main.grid, cells, FULL);
    else main.grid.replaceChildren();
    editor.openButton.textContent = hasSelection ? `編輯課表(${selected.size})` : '編輯課表';
  }

  /* ---------- Editor ---------- */

  function setTab(name, focus) {
    activeTab = name;
    editor.tabs.forEach(({ name: tabName, tab, panel }) => {
      const on = tabName === name;
      tab.setAttribute('aria-selected', String(on));
      tab.tabIndex = on ? 0 : -1;
      panel.hidden = !on && !(wide.matches && tabName === 'preview');
      if (on && focus) tab.focus();
    });
  }

  function syncLayout() {
    if (wide.matches && activeTab === 'preview') setTab('pick');
    else setTab(activeTab);
  }

  function clashingCourseIds() {
    const taken = new Map();
    draft.forEach((id) => {
      courseById.get(id).slots.forEach((slot) => taken.set(`${slot.day}-${slot.period}`, id));
    });
    return (course) =>
      !draft.has(course.id) && course.slots.some((slot) => taken.has(`${slot.day}-${slot.period}`));
  }

  function toggleDraft(id, on) {
    if (on) draft.add(id);
    else draft.delete(id);
    refreshCourseList();
    renderDraftList();
    renderPreview();
    renderFooter();
  }

  function renderCourseList() {
    const classId = Number(editor.classSelect.value);
    courseRefs.clear();
    editor.courseList.replaceChildren();
    data.courses.filter((course) => course.classId === classId).forEach((course) => {
      const item = el('li');
      const label = el('label', 'course-option');
      const box = el('input');
      box.type = 'checkbox';
      box.addEventListener('change', () => toggleDraft(course.id, box.checked));
      const text = el('span', 'course-option__text');
      const clash = el('small', 'course-option__clash', '與已選課程時段衝突');
      text.append(el('strong', '', course.name), el('small', '', `${course.teacher}・${slotText(course) || '未排時段'}`), clash);
      label.append(box, text);
      item.append(label);
      editor.courseList.append(item);
      courseRefs.set(course.id, { box, clash });
    });
    refreshCourseList();
  }

  function refreshCourseList() {
    const clashes = clashingCourseIds();
    courseRefs.forEach(({ box, clash }, id) => {
      box.checked = draft.has(id);
      clash.hidden = !clashes(courseById.get(id));
    });
  }

  function renderDraftList() {
    editor.draftList.replaceChildren();
    const ids = Array.from(draft);
    editor.draftEmpty.hidden = ids.length > 0;
    editor.clearButton.hidden = ids.length === 0;
    ids.map((id) => courseById.get(id)).forEach((course) => {
      const item = el('li');
      const text = el('span');
      text.append(el('strong', '', course.name), el('small', '', `${course.className}・${course.teacher}・${slotText(course)}`));
      const remove = el('button', 'btn btn--quiet', '移除');
      remove.type = 'button';
      remove.setAttribute('aria-label', `移除 ${course.name}`);
      remove.addEventListener('click', () => {
        const buttons = Array.from(editor.draftList.querySelectorAll('button'));
        const index = buttons.indexOf(remove);
        toggleDraft(course.id, false);
        const next = editor.draftList.querySelectorAll('button')[Math.min(index, draft.size - 1)];
        (next || editor.tabs[1].tab).focus();
      });
      item.append(text, remove);
      editor.draftList.append(item);
    });
  }

  function renderPreview() {
    const cells = buildCells(draft);
    const clashes = findClashes(cells);
    const hasDraft = draft.size > 0;
    editor.previewEmpty.hidden = hasDraft;
    editor.previewGrid.hidden = !hasDraft;
    editor.conflicts.hidden = clashes.length === 0;
    if (clashes.length) editor.conflicts.textContent = `有 ${clashes.length} 個時段衝突。${clashes.join(';')}`;
    if (hasDraft) renderGrid(editor.previewGrid, cells, COMPACT);
    else editor.previewGrid.replaceChildren();
  }

  function renderFooter() {
    const added = Array.from(draft).filter((id) => !selected.has(id)).length;
    const removed = Array.from(selected).filter((id) => !draft.has(id)).length;
    const changed = added + removed > 0;
    editor.diff.textContent = changed
      ? [added ? `新增 ${added} 門` : '', removed ? `移除 ${removed} 門` : ''].filter(Boolean).join('、') + `,共 ${draft.size} 門`
      : `沒有變更,目前 ${draft.size} 門課`;
    editor.saveButton.disabled = !changed;
    editor.draftCount.textContent = `(${draft.size})`;
    return changed;
  }

  function renderEditor() {
    renderCourseList();
    renderDraftList();
    renderPreview();
    renderFooter();
  }

  function isDirty() {
    return renderFooter();
  }

  function openEditor() {
    draft = new Set(selected);
    const lastId = Array.from(draft).pop();
    editor.classSelect.value = lastId ? courseById.get(lastId).classId : data.classes[0]?.id;
    setTab('pick');
    renderEditor();
    editor.dialog.showModal();
  }

  function closeEditor(force) {
    if (!force && isDirty() && !window.confirm('有尚未儲存的變更,確定要放棄嗎?')) return;
    editor.dialog.close();
  }

  function saveEditor() {
    selected = new Set(draft);
    save();
    renderMain();
    editor.dialog.close();
  }

  function initEditor() {
    data.classes.forEach((item) => {
      const option = el('option', '', item.name);
      option.value = item.id;
      editor.classSelect.append(option);
    });
    editor.openButton.addEventListener('click', openEditor);
    editor.cancelButton.addEventListener('click', () => closeEditor(false));
    editor.saveButton.addEventListener('click', saveEditor);
    editor.clearButton.addEventListener('click', () => {
      draft = new Set();
      renderEditor();
      editor.tabs[1].tab.focus();
    });
    editor.classSelect.addEventListener('change', renderCourseList);
    editor.dialog.addEventListener('cancel', (event) => {
      event.preventDefault();
      closeEditor(false);
    });

    editor.tabs.forEach(({ name, tab }, index) => {
      tab.addEventListener('click', () => setTab(name));
      tab.addEventListener('keydown', (event) => {
        const visible = editor.tabs.filter((item) => !(wide.matches && item.name === 'preview'));
        const position = visible.findIndex((item) => item.name === name);
        const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
        if (!step) return;
        event.preventDefault();
        setTab(visible[(position + step + visible.length) % visible.length].name, true);
      });
    });
    wide.addEventListener('change', syncLayout);
  }

  initEditor();
  renderMain();
})();

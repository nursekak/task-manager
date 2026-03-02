const API = '/v1';
const TOKEN_KEY = 'task_manager_token';
const EMAIL_KEY = 'task_manager_email';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setAuth(token, email) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(EMAIL_KEY, email || '');
  } else {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
  }
}

function getAuthHeaders() {
  const t = getToken();
  return t ? { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

function getErrorMessage(err) {
  const d = err?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d) && d.length > 0) {
    const first = d[0];
    const msg = first.msg || first.message;
    const loc = first.loc ? first.loc.slice(1).join('.') : '';
    return loc ? `${loc}: ${msg}` : (msg || JSON.stringify(first));
  }
  if (err?.status === 500) return err?.data?.detail || 'Ошибка сервера. Попробуйте позже.';
  if (err?.status) return 'Ошибка запроса (код ' + err.status + ')';
  return 'Ошибка запроса';
}

async function api(method, path, body) {
  const opts = { method, headers: getAuthHeaders() };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  const text = await r.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (_) {}
  if (!r.ok) throw { status: r.status, data, rawText: text };
  return data;
}

// --- UI ---
const authScreen = document.getElementById('auth-screen');
const tasksScreen = document.getElementById('tasks-screen');
const authError = document.getElementById('auth-error');
const tasksError = document.getElementById('tasks-error');
const userEmailEl = document.getElementById('user-email');
const taskList = document.getElementById('task-list');
const paginationEl = document.getElementById('pagination');

function showError(el, msg) {
  el.textContent = msg || '';
  el.classList.toggle('hidden', !msg);
}

function switchScreen(loggedIn) {
  authScreen.classList.toggle('hidden', loggedIn);
  tasksScreen.classList.toggle('hidden', !loggedIn);
  if (loggedIn) {
    userEmailEl.textContent = localStorage.getItem(EMAIL_KEY) || '';
    loadTasks();
  }
}

// Tabs
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.dataset.tab;
    document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
    showError(authError, '');
  });
});

// Login
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  showError(authError, '');
  const form = e.target;
  const email = form.email.value.trim();
  const password = form.password.value;
  try {
    const data = await api('POST', '/auth/login', { email, password });
    setAuth(data.access_token, email);
    switchScreen(true);
  } catch (err) {
    showError(authError, getErrorMessage(err));
  }
});

// Register
document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  showError(authError, '');
  const form = e.target;
  const email = form.email.value.trim();
  const password = form.password.value;
  try {
    await api('POST', '/auth/register', { email, password });
    const data = await api('POST', '/auth/login', { email, password });
    setAuth(data.access_token, email);
    switchScreen(true);
  } catch (err) {
    showError(authError, getErrorMessage(err));
  }
});

// Logout
document.getElementById('logout-btn').addEventListener('click', () => {
  setAuth(null);
  switchScreen(false);
});

// Tasks state
let currentPage = 1;
let currentStatus = '';
const limit = 10;

function statusLabel(s) {
  const v = { pending: 'Ожидает', in_progress: 'В работе', done: 'Готово' };
  return v[s] || s;
}

async function loadTasks() {
  showError(tasksError, '');
  let path = `/tasks/?page=${currentPage}&limit=${limit}`;
  if (currentStatus) path += `&status=${currentStatus}`;
  try {
    const data = await api('GET', path);
    renderTasks(data.items);
    renderPagination(data.page, data.pages, data.total);
  } catch (err) {
    if (err.status === 401) {
      setAuth(null);
      switchScreen(false);
      return;
    }
    showError(tasksError, getErrorMessage(err));
  }
}

function renderTasks(items) {
  taskList.innerHTML = items.length === 0
    ? '<li class="task-item" style="justify-content:center;color:var(--text-dim)">Нет задач</li>'
    : items.map(t => `
      <li class="task-item ${t.status === 'done' ? 'done' : ''}" data-id="${t.id}">
        <div class="task-body">
          <div class="task-title">${escapeHtml(t.title)}</div>
          ${t.description ? `<div class="task-description">${escapeHtml(t.description)}</div>` : ''}
          <div class="task-meta">
            <span class="status-badge status-${t.status}">${statusLabel(t.status)}</span>
            · ${formatDate(t.updated_at)}
          </div>
        </div>
        <div class="task-actions">
          <button type="button" class="btn edit-btn" data-id="${t.id}">Изменить</button>
          <button type="button" class="btn delete-btn" data-id="${t.id}">Удалить</button>
        </div>
      </li>
    `).join('');
  taskList.querySelectorAll('.edit-btn').forEach(btn => {
    btn.addEventListener('click', () => openEdit(Number(btn.dataset.id)));
  });
  taskList.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', () => deleteTask(Number(btn.dataset.id)));
  });
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function formatDate(s) {
  if (!s) return '';
  const d = new Date(s);
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function renderPagination(page, pages, total) {
  if (pages <= 1) {
    paginationEl.innerHTML = total ? `<span>Всего: ${total}</span>` : '';
    return;
  }
  paginationEl.innerHTML = `
    <button type="button" data-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>Назад</button>
    <span>Стр. ${page} из ${pages} (всего ${total})</span>
    <button type="button" data-page="${page + 1}" ${page >= pages ? 'disabled' : ''}>Вперёд</button>
  `;
  paginationEl.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      currentPage = Number(btn.dataset.page);
      loadTasks();
    });
  });
}

// Add task
document.getElementById('add-task-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  showError(tasksError, '');
  const form = e.target;
  const payload = {
    title: form.title.value.trim(),
    description: form.description.value.trim() || null,
    status: form.status.value
  };
  try {
    await api('POST', '/tasks/', payload);
    form.title.value = '';
    form.description.value = '';
    loadTasks();
  } catch (err) {
    showError(tasksError, getErrorMessage(err));
  }
});

// Filter
document.getElementById('apply-filter').addEventListener('click', () => {
  currentStatus = document.getElementById('filter-status').value;
  currentPage = 1;
  loadTasks();
});

// Edit modal
const editModal = document.getElementById('edit-modal');
const editForm = document.getElementById('edit-task-form');

function openEdit(id) {
  api('GET', `/tasks/${id}`).then(task => {
    editForm.id.value = task.id;
    editForm.title.value = task.title;
    editForm.description.value = task.description || '';
    editForm.status.value = task.status;
    editModal.classList.remove('hidden');
  }).catch(() => showError(tasksError, 'Не удалось загрузить задачу'));
}

function closeEdit() {
  editModal.classList.add('hidden');
}

document.getElementById('cancel-edit').addEventListener('click', closeEdit);
editModal.addEventListener('click', (e) => { if (e.target === editModal) closeEdit(); });

editForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = editForm.id.value;
  const payload = {
    title: editForm.title.value.trim(),
    description: editForm.description.value.trim() || null,
    status: editForm.status.value
  };
  try {
    await api('PATCH', `/tasks/${id}`, payload);
    closeEdit();
    loadTasks();
  } catch (err) {
    showError(tasksError, getErrorMessage(err));
  }
});

async function deleteTask(id) {
  if (!confirm('Удалить задачу?')) return;
  try {
    await api('DELETE', `/tasks/${id}`);
    loadTasks();
  } catch (err) {
    showError(tasksError, getErrorMessage(err));
  }
}

// Init
if (getToken()) {
  switchScreen(true);
} else {
  switchScreen(false);
}

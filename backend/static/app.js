/* ===== Library AI System — Frontend App ===== */

const API = '/api';
let token = localStorage.getItem('lib_token') || null;
let currentUser = null;
let chatSessionId = null;

// ─── Init ───
document.addEventListener('DOMContentLoaded', async () => {
    if (token) {
        await loadProfile(true);
    } else {
        updateAuthUI();
    }
    loadBooks();
});

// ─── API Helpers ───
function headers(json = true) {
    const h = {};
    if (json) h['Content-Type'] = 'application/json';
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
}

async function apiGet(url) {
    const res = await fetch(API + url, { headers: headers() });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw err;
    }
    return res.json();
}

async function apiPost(url, body) {
    const res = await fetch(API + url, {
        method: 'POST', headers: headers(), body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw err;
    }
    return res.json();
}

// ─── Pages ───
function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const page = document.getElementById('page-' + name);
    if (page) page.classList.add('active');
    const link = document.querySelector(`.nav-link[data-page="${name}"]`);
    if (link) link.classList.add('active');
    if (name === 'books') loadBooks();
    if (name === 'admin') loadAdminDashboard();
}

// ─── Auth ───
async function doLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    errEl.textContent = '';

    if (!email || !password) {
        errEl.textContent = 'Please enter email and password';
        return;
    }

    try {
        const data = await apiPost('/auth/login', { email, password });
        token = data.access_token;
        localStorage.setItem('lib_token', token);

        // Confirm token works before declaring success.
        const profileOk = await loadProfile(true);
        if (!profileOk) {
            errEl.textContent = 'Sign in could not be completed. Please try again.';
            toast('Sign in failed. Please try again.', 'error');
            return;
        }

        hideModal('login');
        document.getElementById('login-password').value = '';
        toast('Signed in successfully!', 'success');
        loadBooks();
    } catch (e) {
        errEl.textContent = e.detail || 'Login failed. Check your email and password.';
    }
}

async function doRegister() {
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const full_name = document.getElementById('reg-fullname').value.trim();
    const password = document.getElementById('reg-password').value;
    const errEl = document.getElementById('reg-error');
    errEl.textContent = '';

    if (!username || !email || !password) {
        errEl.textContent = 'Please fill in all required fields';
        return;
    }

    try {
        await apiPost('/auth/register', { username, email, full_name, password });
        hideModal('register');
        toast('Account created! Please sign in.', 'success');
        showModal('login');
    } catch (e) {
        errEl.textContent = e.detail || 'Registration failed';
    }
}

function logout() {
    const onAdminPage = document.getElementById('page-admin')?.classList.contains('active');
    token = null;
    currentUser = null;
    localStorage.removeItem('lib_token');
    updateAuthUI();
    if (onAdminPage) showPage('home');
    toast('Signed out', 'info');
}

function updateAuthUI() {
    const adminLink = document.getElementById('nav-admin-link');
    if (token && currentUser) {
        document.getElementById('auth-section-logged-in').style.display = 'flex';
        document.getElementById('auth-section-logged-out').style.display = 'none';
        document.getElementById('user-badge').textContent = `👤 ${currentUser.username || currentUser.email}`;
        // Show upload for admin (case-insensitive)
        const role = (currentUser.role || '').toLowerCase();
        document.getElementById('upload-btn').style.display = (role === 'admin') ? 'inline-flex' : 'none';
        if (adminLink) adminLink.style.display = (role === 'admin') ? 'inline-flex' : 'none';
    } else {
        document.getElementById('auth-section-logged-in').style.display = 'none';
        document.getElementById('auth-section-logged-out').style.display = 'flex';
        document.getElementById('upload-btn').style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
    }
}

async function loadProfile(silent = false) {
    if (!token) { updateAuthUI(); return false; }
    try {
        currentUser = await apiGet('/auth/me');
        updateAuthUI();
        return true;
    } catch (e) {
        console.warn('Profile load failed:', e);
        // Token might be expired — clear it silently
        token = null;
        currentUser = null;
        localStorage.removeItem('lib_token');
        updateAuthUI();
        if (!silent) {
            toast('Session expired. Please sign in again.', 'info');
        }
        return false;
    }
}

// ─── Books ───
async function loadAdminDashboard() {
    const role = (currentUser?.role || '').toLowerCase();
    const tbody = document.getElementById('admin-borrow-rows');

    if (!token || role !== 'admin') {
        if (tbody) tbody.innerHTML = '<tr><td colspan="8">Admin access required.</td></tr>';
        return;
    }

    try {
        const [dashboardRes, borrowRes] = await Promise.allSettled([
            apiGet('/dashboard/'),
            apiGet('/borrow/admin/history?limit=100'),
        ]);

        if (dashboardRes.status === 'fulfilled') {
            const overview = dashboardRes.value.overview || {};
            document.getElementById('admin-total-books').textContent = overview.total_books ?? 0;
            document.getElementById('admin-total-users').textContent = overview.total_users ?? 0;
            document.getElementById('admin-total-borrows').textContent = overview.total_borrows ?? 0;
            document.getElementById('admin-active-borrows').textContent = overview.active_borrows ?? 0;
            document.getElementById('admin-overdue-borrows').textContent = overview.overdue_borrows ?? 0;
            document.getElementById('admin-books-pending').textContent = overview.books_pending ?? 0;
            document.getElementById('stat-users').textContent = overview.total_users ?? 0;
            document.getElementById('stat-borrows').textContent = overview.total_borrows ?? 0;
        }

        if (borrowRes.status !== 'fulfilled') {
            throw borrowRes.reason || new Error('Failed to load borrow records');
        }

        const rows = borrowRes.value.records || [];
        if (!rows.length) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="8">No borrow records found.</td></tr>';
            return;
        }

        if (tbody) {
            tbody.innerHTML = rows.map((record) => {
                const statusRaw = (record.status || 'unknown').toLowerCase();
                const statusClass = `admin-status admin-status-${statusRaw}`;
                const returnBtn = statusRaw === 'issued' ? `<button class="btn btn-sm btn-outline" onclick="adminReturnBook(${record.id})">Return</button>` : '-';
                return `
                    <tr>
                        <td>${esc(record.username || `User #${record.user_id}`)}</td>
                        <td>${esc(record.user_email || '-')}</td>
                        <td>${esc(record.book_title || 'Unknown')}</td>
                        <td>${record.copy_number ?? '-'}</td>
                        <td>${formatDateTime(record.issued_at)}</td>
                        <td>${formatDateTime(record.due_date)}</td>
                        <td><span class="${statusClass}">${esc(statusRaw)}</span></td>
                        <td>${returnBtn}</td>
                    </tr>
                `;
            }).join('');
        }
    } catch (e) {
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="8" style="color:var(--danger)">${esc(e.detail || 'Failed to load admin dashboard')}</td></tr>`;
        }
    }
}

async function adminReturnBook(borrowId) {
    if (!confirm('Are you sure you want to forcefully return this book?')) return;
    try {
        await apiPost('/borrow/return', { borrow_id: borrowId });
        toast('Book returned successfully', 'success');
        loadAdminDashboard();
    } catch (e) {
        toast(e.detail || 'Failed to return book', 'error');
    }
}

async function loadBooks() {
    const grid = document.getElementById('books-grid');
    const search = document.getElementById('book-search-input')?.value || '';
    try {
        const data = await apiGet(`/books/?page=1&per_page=50${search ? '&search=' + encodeURIComponent(search) : ''}`);
        const books = data.books || data.items || data;
        if (!books || books.length === 0) {
            grid.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><h3>No books yet</h3><p>Sign in as admin and upload your first book!</p></div>`;
            return;
        }
        grid.innerHTML = books.map(b => `
            <div class="book-card" onclick="showBookDetail(${b.id})">
                <div class="book-cover">📖
                    <span class="book-status status-${b.ingestion_status || 'pending'}">${b.ingestion_status || 'pending'}</span>
                </div>
                <div class="book-info">
                    <h3>${esc(b.title)}</h3>
                    <div class="book-author">${esc(b.author || 'Unknown')}</div>
                    <div class="book-meta">
                        <span class="book-copies">${b.available_copies ?? '?'}/${b.total_copies ?? '?'} copies</span>
                        <div class="book-actions">
                            <button class="btn btn-sm btn-outline" onclick="event.stopPropagation();openPdfReader(${b.id})">Read</button>
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation();borrowBook(${b.id})">Borrow</button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Update chat book select and preserve current scope if possible.
        const sel = document.getElementById('chat-book-select');
        const previousValue = sel.value;
        sel.innerHTML = '<option value="">All books</option>' + books.map(b => `<option value="${b.id}">${esc(b.title)}</option>`).join('');
        if (previousValue && books.some(b => String(b.id) === String(previousValue))) {
            sel.value = previousValue;
        }

        // Update home stats
        document.getElementById('stat-books').textContent = books.length;
    } catch (e) {
        console.error('Failed to load books:', e);
        grid.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Could not load books</h3><p>${e.detail || 'Server error. Is the backend running?'}</p></div>`;
    }
}

function searchBooks() { clearTimeout(window._searchTimer); window._searchTimer = setTimeout(loadBooks, 300); }

async function showBookDetail(id) {
    const el = document.getElementById('book-detail-content');
    el.innerHTML = '<p style="text-align:center;padding:2rem;">Loading...</p>';
    showModal('bookdetail');
    try {
        const book = await apiGet(`/books/${id}`);
        el.innerHTML = `
            <div class="book-detail-header">
                <div class="book-detail-cover">📖</div>
                <div class="book-detail-info">
                    <h2>${esc(book.title)}</h2>
                    <div class="author">by ${esc(book.author || 'Unknown')}</div>
                    <div class="description">${esc(book.description || 'No description.')}</div>
                    <p style="font-size:0.85rem;color:var(--text-muted)">
                        Pages: ${book.total_pages || '?'} · Copies: ${book.available_copies}/${book.total_copies} · Status: ${book.ingestion_status}
                        ${book.isbn ? ' · ISBN: ' + book.isbn : ''}
                    </p>
                    <div class="detail-actions">
                        <button class="btn btn-outline" onclick="openPdfReader(${book.id})">👀 Read</button>
                        <button class="btn btn-primary" onclick="borrowBook(${book.id})">📖 Borrow</button>
                        <button class="btn btn-outline" onclick="getSummary(${book.id})">📋 Summary</button>
                    </div>
                </div>
            </div>
            <div class="detail-section">
                <h3>❓ Ask a Question</h3>
                <div class="qa-form">
                    <input type="text" id="qa-input-${book.id}" placeholder="Ask anything about this book...">
                    <button class="btn btn-primary" onclick="askQuestion(${book.id})">Ask</button>
                </div>
                <div id="qa-answer-${book.id}" class="qa-answer" style="display:none"></div>
            </div>
            <div class="detail-section" id="summary-section-${book.id}"></div>
        `;
    } catch (e) {
        el.innerHTML = `<p style="color:var(--danger)">Failed to load book details.</p>`;
    }
}

async function borrowBook(bookId) {
    if (!token) { showModal('login'); return; }
    try {
        await apiPost('/borrow/', { book_id: bookId });
        toast('Book borrowed successfully!', 'success');
        loadBooks();
    } catch (e) {
        toast(e.detail || 'Failed to borrow', 'error');
    }
}

async function askQuestion(bookId) {
    const input = document.getElementById('qa-input-' + bookId);
    const answerEl = document.getElementById('qa-answer-' + bookId);
    if (!input.value.trim()) return;
    if (!token) { showModal('login'); return; }
    answerEl.style.display = 'block';
    answerEl.innerHTML = '⏳ Thinking...';
    try {
        const data = await apiPost('/ai/qa', { question: input.value, book_id: bookId });
        answerEl.innerHTML = `<div class="markdown-body"><strong>Answer:</strong><br>${renderMarkdown(data.answer)}</div>`;
    } catch (e) {
        answerEl.innerHTML = `<span style="color:var(--danger)">${e.detail || 'Failed to get answer'}</span>`;
    }
}

async function getSummary(bookId) {
    if (!token) { showModal('login'); return; }
    const section = document.getElementById('summary-section-' + bookId);
    section.innerHTML = '<h3>📋 Summary</h3><p>⏳ Generating summary...</p>';
    try {
        const data = await apiPost('/ai/summary', { book_id: bookId });
        let html = `<h3>📋 Summary ${data.is_cached ? '(cached)' : ''}</h3><div class="markdown-body">${renderMarkdown(data.summary)}</div>`;
        if (data.key_ideas && data.key_ideas.length) {
            html += '<h4 style="margin-top:1rem;">Key Ideas</h4><div class="markdown-body"><ul>' + data.key_ideas.map(i => `<li>${renderMarkdown(i)}</li>`).join('') + '</ul></div>';
        }
        section.innerHTML = html;
    } catch (e) {
        section.innerHTML = `<h3>📋 Summary</h3><p style="color:var(--danger)">${e.detail || 'Failed to generate summary'}</p>`;
    }
}

// ─── Upload ───
function onFileSelected() {
    const file = document.getElementById('upload-file').files[0];
    if (file) document.getElementById('file-label').textContent = `📄 ${file.name}`;
}

async function doUpload() {
    if (!token) { showModal('login'); return; }
    const file = document.getElementById('upload-file').files[0];
    const title = document.getElementById('upload-title').value;
    const errEl = document.getElementById('upload-error');
    errEl.textContent = '';
    if (!file || !title) { errEl.textContent = 'Title and PDF file are required'; return; }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('author', document.getElementById('upload-author').value || 'Unknown');
    formData.append('description', document.getElementById('upload-desc').value || '');
    formData.append('total_copies', document.getElementById('upload-copies').value || '1');

    document.getElementById('upload-progress').style.display = 'block';
    document.getElementById('progress-fill').style.width = '30%';
    document.getElementById('progress-text').textContent = 'Uploading...';

    try {
        const res = await fetch(API + '/books/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
        });
        document.getElementById('progress-fill').style.width = '100%';
        if (!res.ok) throw await res.json();
        document.getElementById('progress-text').textContent = 'Complete!';
        setTimeout(() => {
            hideModal('upload');
            document.getElementById('upload-progress').style.display = 'none';
            document.getElementById('progress-fill').style.width = '0%';
        }, 800);
        toast('Book uploaded! Ingestion started.', 'success');
        loadBooks();
    } catch (e) {
        errEl.textContent = e.detail || 'Upload failed';
        document.getElementById('upload-progress').style.display = 'none';
    }
}

// ─── Chat ───
function onChatScopeChange() {
    const bookSel = document.getElementById('chat-book-select');
    if (!bookSel) return;

    // New scope should start a fresh conversation thread.
    chatSessionId = null;

    if (!bookSel.value) {
        addChatMsg('Scope cleared. Ask me anything across all books.', 'bot');
        return;
    }

    const title = bookSel.options[bookSel.selectedIndex]?.text || 'this book';
    addChatMsg(`You chose "${title}". What do you want to know about it?`, 'bot');
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    if (!token) { showModal('login'); return; }

    input.value = '';
    addChatMsg(msg, 'user');

    const bookSel = document.getElementById('chat-book-select');
    const bookId = bookSel.value ? parseInt(bookSel.value) : null;

    const body = { message: msg };
    if (chatSessionId) body.session_id = chatSessionId;
    if (bookId) body.book_id = bookId;

    const thinkingId = addChatMsg('⏳ Thinking...', 'bot');

    try {
        const data = await apiPost('/ai/chat/', body);
        chatSessionId = data.session_id;
        removeChatMsg(thinkingId);
        addChatMsg(data.response, 'bot');
    } catch (e) {
        removeChatMsg(thinkingId);
        addChatMsg('❌ ' + (e.detail || 'Failed to get response'), 'bot');
    }
}

function addChatMsg(text, role) {
    const id = 'msg-' + Date.now() + Math.random();
    const container = document.getElementById('chat-messages');
    const avatar = role === 'bot' ? '🤖' : '👤';
    const content = role === 'bot' ? renderMarkdown(text) : esc(text);
    container.innerHTML += `<div class="chat-msg ${role}" id="${id}"><div class="msg-avatar">${avatar}</div><div class="msg-content ${role === 'bot' ? 'markdown-body' : ''}">${content}</div></div>`;
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeChatMsg(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ─── Search ───
async function doSearch() {
    const query = document.getElementById('semantic-search-input').value.trim();
    if (!query) return;
    if (!token) { showModal('login'); return; }

    const container = document.getElementById('search-results');
    container.innerHTML = '<p style="text-align:center;padding:2rem;">🔍 Searching...</p>';

    try {
        const data = await apiGet(`/search/?q=${encodeURIComponent(query)}&top_k=10`);
        const results = data.results || [];
        if (!results.length) {
            container.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><h3>No results found</h3></div>';
            return;
        }
        container.innerHTML = results.map(r => `
            <div class="search-result-card" style="cursor: pointer;" onclick="openPdfReader(${r.book_id}, ${r.page_number || 1})">
                <h4>📖 ${esc(r.book_title)} ${r.page_number ? '— Page ' + r.page_number : ''}</h4>
                <p>${esc(r.chunk_text)}</p>
                <div class="result-meta">Relevance: ${(r.relevance_score * 100).toFixed(1)}%</div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<p style="color:var(--danger);text-align:center">${e.detail || 'Search failed'}</p>`;
    }
}

// ─── Modals ───
function showModal(name) { document.getElementById('modal-' + name).classList.add('active'); }

// ─── PDF Reader ───
function openPdfReader(bookId, pageNumber = null) {
    const frame = document.getElementById('pdf-frame');
    document.getElementById('pdf-title').textContent = `Reading Book`;
    let url = `/api/books/${bookId}/pdf`;
    if (pageNumber) {
        url += `#page=${pageNumber}`;
    }
    frame.src = url;
    showModal('pdf');
}
function hideModal(name) { document.getElementById('modal-' + name).classList.remove('active'); }
function closeModal(event, name) { if (event.target === event.currentTarget) hideModal(name); }

// ─── Toast ───
function toast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

// ─── Util ───
function esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function renderMarkdown(str) {
    if (!str) return '';
    if (typeof marked !== 'undefined') {
        try {
            return marked.parse(str);
        } catch (e) {
            console.warn('Markdown parsing failed', e);
        }
    }
    return esc(str).replace(/\n/g, '<br>');
}

function formatDateTime(value) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleString();
}

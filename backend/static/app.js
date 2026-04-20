/* ===== Library AI System — Frontend App ===== */

const API = '/api';
let token = localStorage.getItem('lib_token') || null;
let currentUser = null;
let chatSessionId = null;

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
    if (token) loadProfile();
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
        hideModal('login');

        // Try to load profile, but don't fail if it errors
        const profileOk = await loadProfile(true);
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
    token = null;
    currentUser = null;
    localStorage.removeItem('lib_token');
    updateAuthUI();
    toast('Signed out', 'info');
}

function updateAuthUI() {
    if (token && currentUser) {
        document.getElementById('auth-section-logged-in').style.display = 'flex';
        document.getElementById('auth-section-logged-out').style.display = 'none';
        document.getElementById('user-badge').textContent = `👤 ${currentUser.username || currentUser.email}`;
        // Show upload for admin (case-insensitive)
        const role = (currentUser.role || '').toLowerCase();
        document.getElementById('upload-btn').style.display = (role === 'admin') ? 'inline-flex' : 'none';
    } else {
        document.getElementById('auth-section-logged-in').style.display = 'none';
        document.getElementById('auth-section-logged-out').style.display = 'flex';
        document.getElementById('upload-btn').style.display = 'none';
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
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation();borrowBook(${b.id})">Borrow</button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Update chat book select
        const sel = document.getElementById('chat-book-select');
        sel.innerHTML = '<option value="">All books</option>' + books.map(b => `<option value="${b.id}">${esc(b.title)}</option>`).join('');

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
        answerEl.innerHTML = `<strong>Answer:</strong><br>${esc(data.answer)}`;
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
        let html = `<h3>📋 Summary ${data.is_cached ? '(cached)' : ''}</h3><p>${esc(data.summary)}</p>`;
        if (data.key_ideas && data.key_ideas.length) {
            html += '<h4 style="margin-top:1rem;">Key Ideas</h4><ul>' + data.key_ideas.map(i => `<li>${esc(i)}</li>`).join('') + '</ul>';
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
    container.innerHTML += `<div class="chat-msg ${role}" id="${id}"><div class="msg-avatar">${avatar}</div><div class="msg-content">${esc(text)}</div></div>`;
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
            <div class="search-result-card">
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

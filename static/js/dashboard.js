// Shortly — Dashboard: AJAX orqali havola yaratish, nusxalash va o'chirish

document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('dashboard-root');
    if (!root) return;

    const form = document.getElementById('shorten-form');
    const input = document.getElementById('original-url-input');
    const submitBtn = document.getElementById('shorten-btn');
    const formError = document.getElementById('form-error');
    const resultBox = document.getElementById('result-box');
    const resultLink = document.getElementById('result-link');
    const resultCopy = document.getElementById('result-copy');
    const tbody = document.getElementById('urls-tbody');
    const table = document.getElementById('urls-table');
    const emptyState = document.getElementById('empty-state');

    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    // --- Qo'shimcha sozlamalar paneli ---
    const advancedToggle = document.getElementById('advanced-toggle');
    const advancedPanel = document.getElementById('advanced-panel');
    const customCodeInput = document.getElementById('custom-code-input');
    const expiresInput = document.getElementById('expires-input');

    advancedToggle.addEventListener('click', () => {
        advancedPanel.classList.toggle('hidden');
    });

    // --- Havola yaratish ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const originalUrl = input.value.trim();
        if (!originalUrl) {
            showError('URL manzilni kiriting.');
            return;
        }

        const body = new URLSearchParams({ original_url: originalUrl });
        if (customCodeInput.value.trim()) body.set('custom_code', customCodeInput.value.trim());
        if (expiresInput.value) body.set('expires_at', expiresInput.value);

        submitBtn.disabled = true;
        try {
            const response = await fetch(root.dataset.shortenUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body,
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                showError((data.errors && data.errors[0]) || 'Xatolik yuz berdi. Qayta urinib ko\'ring.');
                return;
            }

            input.value = '';
            customCodeInput.value = '';
            expiresInput.value = '';
            showResult(data.url);
            prependRow(data.url);
            bumpStat('stat-total-urls', 1);
            updateCount(1);
            recalcTopClicks();
            toggleEmptyState();
        } catch (err) {
            showError('Server bilan bog\'lanishda xatolik. Qayta urinib ko\'ring.');
        } finally {
            submitBtn.disabled = false;
        }
    });

    // --- Jadvaldagi tugmalar (delegatsiya) ---
    document.addEventListener('click', async (e) => {
        const copyBtn = e.target.closest('.copy-btn');
        if (copyBtn) {
            await copyToClipboard(copyBtn.dataset.url, copyBtn);
            return;
        }

        const toggleBtn = e.target.closest('.toggle-btn');
        if (toggleBtn) {
            await toggleUrl(toggleBtn);
            return;
        }

        const qrBtn = e.target.closest('.qr-btn');
        if (qrBtn) {
            openQrModal(qrBtn.dataset.qrUrl, qrBtn.dataset.code);
            return;
        }

        const deleteBtn = e.target.closest('.delete-btn');
        if (deleteBtn) {
            if (!confirm('Bu havolani o\'chirishni tasdiqlaysizmi?')) return;
            await deleteUrl(deleteBtn);
        }
    });

    // --- QR modal ---
    const qrModal = document.getElementById('qr-modal');
    document.getElementById('qr-close').addEventListener('click', closeQrModal);
    document.getElementById('qr-backdrop').addEventListener('click', closeQrModal);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeQrModal();
    });

    function openQrModal(qrUrl, code) {
        document.getElementById('qr-image').src = qrUrl;
        document.getElementById('qr-code-label').textContent = window.location.host + '/' + code + '/';
        const download = document.getElementById('qr-download');
        download.href = qrUrl;
        download.download = 'qr-' + code + '.png';
        qrModal.classList.remove('hidden');
        qrModal.classList.add('flex');
    }

    function closeQrModal() {
        qrModal.classList.add('hidden');
        qrModal.classList.remove('flex');
    }

    async function toggleUrl(btn) {
        btn.disabled = true;
        try {
            const response = await fetch(btn.dataset.toggleUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
            });
            const data = await response.json();
            if (data.success) {
                btn.textContent = data.is_active ? 'To\'xtatish' : 'Faollashtirish';
                const badge = btn.closest('tr').querySelector('.status-badge');
                applyStatusBadge(badge, data.status);
            }
        } catch (err) {
            alert('Holatni o\'zgartirishda xatolik yuz berdi.');
        } finally {
            btn.disabled = false;
        }
    }

    resultCopy.addEventListener('click', () => copyToClipboard(resultLink.href, resultCopy));

    // --- Yordamchi funksiyalar ---

    async function deleteUrl(btn) {
        btn.disabled = true;
        try {
            const response = await fetch(btn.dataset.deleteUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
            });
            const data = await response.json();
            if (data.success) {
                const row = btn.closest('tr');
                const clicks = parseInt(row.querySelector('.clicks-badge').textContent, 10) || 0;
                row.remove();
                bumpStat('stat-total-urls', -1);
                bumpStat('stat-total-clicks', -clicks);
                updateCount(-1);
                recalcTopClicks();
                toggleEmptyState();
            }
        } catch (err) {
            alert('O\'chirishda xatolik yuz berdi.');
        } finally {
            btn.disabled = false;
        }
    }

    function prependRow(url) {
        const tr = document.createElement('tr');
        tr.dataset.code = url.short_code;
        tr.className = 'hover:bg-slate-800/30 transition';
        tr.innerHTML = `
            <td class="px-6 py-4">
                <a href="${url.short_url}" target="_blank" rel="noopener"
                   class="font-mono text-indigo-300 hover:text-indigo-200">${url.short_code}</a>
            </td>
            <td class="px-6 py-4 max-w-xs">
                <span class="block truncate text-slate-300"></span>
            </td>
            <td class="px-6 py-4 text-center">
                <span class="status-badge inline-block px-2.5 py-1 rounded-full text-xs font-semibold"></span>
            </td>
            <td class="px-6 py-4 text-center">
                <span class="inline-block px-2.5 py-1 rounded-full text-xs font-semibold bg-violet-500/15 text-violet-300 clicks-badge">0</span>
            </td>
            <td class="px-6 py-4 text-slate-400">${url.created_at}</td>
            <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-2">
                    <a href="/stats/${url.short_code}/"
                       class="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-violet-500/20 hover:text-violet-300 border border-slate-700 transition">📊</a>
                    <button type="button" class="qr-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-sky-500/20 hover:text-sky-300 border border-slate-700 transition"
                            data-qr-url="/api/urls/${url.short_code}/qr/" data-code="${url.short_code}" title="QR-kod">QR</button>
                    <button type="button" class="copy-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-indigo-500/20 hover:text-indigo-300 border border-slate-700 transition"
                            data-url="${url.short_url}">Nusxalash</button>
                    <button type="button" class="toggle-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-amber-500/20 hover:text-amber-300 border border-slate-700 transition"
                            data-toggle-url="/api/urls/${url.short_code}/toggle/">${url.is_active ? "To'xtatish" : 'Faollashtirish'}</button>
                    <button type="button" class="delete-btn px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-red-500/20 hover:text-red-300 border border-slate-700 transition"
                            data-delete-url="/api/urls/${url.short_code}/delete/">O'chirish</button>
                </div>
            </td>`;
        // Asl URL matn sifatida qo'yiladi (XSS'dan himoya)
        const span = tr.querySelector('td:nth-child(2) span');
        span.textContent = url.original_url;
        span.title = url.original_url;
        // Holat badge'i
        const badge = tr.querySelector('.status-badge');
        applyStatusBadge(badge, url.status);
        if (url.expires_at) badge.title = 'Muddati: ' + url.expires_at;
        tbody.prepend(tr);
    }

    function applyStatusBadge(badge, status) {
        const styles = {
            active: ['Faol', 'bg-emerald-500/15', 'text-emerald-300'],
            expired: ['Muddati tugagan', 'bg-red-500/15', 'text-red-300'],
            inactive: ["To'xtatilgan", 'bg-amber-500/15', 'text-amber-300'],
        };
        const [label, bg, color] = styles[status] || styles.inactive;
        badge.classList.remove(
            'bg-emerald-500/15', 'text-emerald-300',
            'bg-red-500/15', 'text-red-300',
            'bg-amber-500/15', 'text-amber-300'
        );
        badge.classList.add(bg, color);
        badge.textContent = label;
    }

    async function copyToClipboard(text, btn) {
        try {
            await navigator.clipboard.writeText(text);
            const original = btn.textContent;
            btn.textContent = '✓ Nusxalandi';
            setTimeout(() => { btn.textContent = original; }, 1500);
        } catch (err) {
            prompt('Havolani qo\'lda nusxalang:', text);
        }
    }

    function showResult(url) {
        resultLink.href = url.short_url;
        resultLink.textContent = url.short_url;
        resultBox.classList.remove('hidden');
        resultBox.classList.add('flex');
    }

    function showError(text) {
        formError.textContent = text;
        formError.classList.remove('hidden');
    }

    function hideError() {
        formError.classList.add('hidden');
    }

    function bumpStat(id, delta) {
        const el = document.getElementById(id);
        el.textContent = Math.max(0, (parseInt(el.textContent, 10) || 0) + delta);
    }

    function updateCount(delta) {
        const el = document.getElementById('urls-count');
        const current = parseInt(el.textContent, 10) || 0;
        el.textContent = Math.max(0, current + delta) + ' ta';
    }

    function recalcTopClicks() {
        const values = [...document.querySelectorAll('#urls-tbody .clicks-badge')]
            .map((b) => parseInt(b.textContent, 10) || 0);
        document.getElementById('stat-top-clicks').textContent = values.length ? Math.max(...values) : 0;
    }

    function toggleEmptyState() {
        const hasRows = tbody.children.length > 0;
        table.style.display = hasRows ? '' : 'none';
        emptyState.style.display = hasRows ? 'none' : '';
    }
});

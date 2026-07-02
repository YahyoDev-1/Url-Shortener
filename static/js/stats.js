// Shortly — Havola statistikasi: Chart.js grafiklari

document.addEventListener('DOMContentLoaded', async () => {
    const root = document.getElementById('stats-root');
    if (!root || typeof Chart === 'undefined') return;

    // Dark tema uchun umumiy Chart.js sozlamalari
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(51, 65, 85, 0.4)';
    Chart.defaults.font.family = 'Inter, sans-serif';

    const PALETTE = ['#818cf8', '#a78bfa', '#34d399', '#38bdf8', '#f472b6', '#fbbf24'];

    // Qisqa havolani nusxalash
    const copyBtn = document.getElementById('copy-short-url');
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(copyBtn.dataset.url);
            const original = copyBtn.textContent;
            copyBtn.textContent = '✓ Nusxalandi';
            setTimeout(() => { copyBtn.textContent = original; }, 1500);
        } catch (err) {
            prompt('Havolani qo\'lda nusxalang:', copyBtn.dataset.url);
        }
    });

    let data;
    try {
        const response = await fetch(root.dataset.statsUrl);
        data = await response.json();
        if (!data.success) throw new Error('API xatosi');
    } catch (err) {
        console.error('Statistikani yuklashda xatolik:', err);
        return;
    }

    // Ko'rsatkichlar
    document.getElementById('stat-total').textContent = data.total_clicks;
    document.getElementById('stat-today').textContent = data.today_clicks;

    // 30 kunlik chiziqli grafik
    new Chart(document.getElementById('daily-chart'), {
        type: 'line',
        data: {
            labels: data.daily.labels,
            datasets: [{
                label: 'Bosishlar',
                data: data.daily.values,
                borderColor: '#818cf8',
                backgroundColor: 'rgba(129, 140, 248, 0.15)',
                fill: true,
                tension: 0.35,
                pointRadius: 3,
                pointBackgroundColor: '#818cf8',
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } },
                x: { ticks: { maxTicksLimit: 10 } },
            },
        },
    });

    renderDoughnut('browser-chart', 'browser-empty', data.browsers);
    renderDoughnut('device-chart', 'device-empty', data.devices);
    renderRecent(data.recent);

    function renderDoughnut(canvasId, emptyId, counts) {
        const canvas = document.getElementById(canvasId);
        const labels = Object.keys(counts);
        if (!labels.length) {
            canvas.parentElement.style.display = 'none';
            document.getElementById(emptyId).classList.remove('hidden');
            return;
        }
        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: labels.map((l) => counts[l]),
                    backgroundColor: PALETTE,
                    borderColor: '#0f172a',
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '62%',
                plugins: { legend: { position: 'bottom' } },
            },
        });
    }

    function renderRecent(items) {
        const list = document.getElementById('recent-list');
        if (!items.length) {
            document.getElementById('recent-empty').classList.remove('hidden');
            return;
        }
        for (const item of items) {
            const li = document.createElement('li');
            li.className = 'flex items-start justify-between gap-3 pb-3 border-b border-slate-800/70';

            const left = document.createElement('div');
            const time = document.createElement('p');
            time.className = 'text-slate-200 font-medium';
            time.textContent = item.time;
            const ref = document.createElement('p');
            ref.className = 'text-xs text-slate-500 truncate max-w-[180px]';
            ref.textContent = item.referrer;
            ref.title = item.referrer;
            left.append(time, ref);

            const right = document.createElement('span');
            right.className = 'shrink-0 px-2 py-1 rounded-md text-xs bg-slate-800 text-slate-300';
            right.textContent = `${item.browser} · ${item.device}`;

            li.append(left, right);
            list.append(li);
        }
    }
});

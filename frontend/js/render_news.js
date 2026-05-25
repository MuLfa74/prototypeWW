function getNewsId(item) {
    return item._id || item.id || item.newsId || '';
}

async function trackNewsOpen(newsId, source) {
    if (!newsId) return;
    try {
        await fetch(`${CONFIG.API_BASE_URL}/stats/track`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({newsId: String(newsId), source: source || 'search'})
        });
    } catch (error) {
        console.error('Failed to track news open:', error);
    }
}

async function loadDailySummary() {
    const container = document.getElementById('daily-summary');
    if (!container) return;

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/news/daily-summary?limit=4`);
        if (!response.ok) throw new Error('summary request failed');
        const payload = await response.json();
        renderDailySummary(container, payload);
    } catch (error) {
        container.innerHTML = '<div class="event">Сводка дня недоступна</div>';
        console.error('Failed to load daily summary:', error);
    }
}

async function loadLastUpdated() {
    const container = document.getElementById('news-last-updated');
    if (!container) return;

    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/news/last-updated`);
        if (!response.ok) throw new Error('last-updated request failed');
        const payload = await response.json();

        if (!payload.last_updated) {
            container.textContent = 'Последнее обновление: пока нет данных';
            return;
        }

        const parsed = new Date(payload.last_updated);
        const formatted = Number.isNaN(parsed.getTime())
            ? payload.last_updated
            : parsed.toLocaleString('ru-RU');

        container.textContent = `Последнее обновление: ${formatted}`;
    } catch (error) {
        container.textContent = 'Последнее обновление: недоступно';
        console.error('Failed to load last updated time:', error);
    }
}

function renderDailySummary(container, payload) {
    const items = payload && Array.isArray(payload.items) ? payload.items : [];
    container.innerHTML = '';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '10px';

    if (items.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'event';
        empty.textContent = 'За последние сутки просмотров нет';
        container.appendChild(empty);
        return;
    }

    items.forEach(item => {
        const row = document.createElement('div');
        row.className = 'event summary-item';
        row.dataset.newsId = item.newsId || '';
        row.innerHTML = `
            <div><strong>${item.header || 'Без названия'}</strong></div>
            <div>${item.clicks || 0} просмотров</div>
        `;
        container.appendChild(row);
    });
}

// Render feed items. Accepts either an array or an object with .content
function renderFeed(data){
    const container = document.getElementById('feed');
    if (!container) return;
    container.innerHTML = '';

    let items = [];
    if (!data) {
        items = [];
    } else if (Array.isArray(data)) {
        items = data;
    } else if (Array.isArray(data.content)) {
        items = data.content;
    } else if (Array.isArray(data.data)) {
        items = data.data;
    }

    if (items.length === 0){
        container.innerHTML = '<center>Упс.. кажется новостей нет(</center>';
        return;
    }

    items.forEach(item => {
        const eventItem = document.createElement('div');
        eventItem.className = 'event';
        eventItem.dataset.newsId = getNewsId(item);

        const header = item.header || item.title || 'Без названия';
        const annotation = item.annotation || item.summary || '';
        const content = item.content || item.full_text || '';

        eventItem.innerHTML = `
            <h2>${header}</h2>
            <div class="annotation">${annotation}</div>
            <div class="full-article">${content}</div>
        `;

        eventItem.addEventListener('click', async () => {
            const contentBlock = eventItem.querySelector('.full-article');
            const annotationBlock = eventItem.querySelector('.annotation');
            contentBlock.classList.toggle('show');
            annotationBlock.classList.toggle('show');
            await trackNewsOpen(eventItem.dataset.newsId, 'search');
        });

        container.appendChild(eventItem);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadDailySummary();
    loadLastUpdated();
});
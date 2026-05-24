let map; 
let selectedCategories = []; 
let allEventsFromServer = [];

async function trackNewsOpen(newsId, source) {
    if (!newsId) return;
    try {
        await fetch(`${CONFIG.API_BASE_URL}/stats/track`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({newsId: String(newsId), source: source || 'feed'})
        });
    } catch (error) {
        console.error('Failed to track marker open:', error);
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

// INIT MAP
ymaps.ready(init);

async function init(){
    // 1. Инициализируем карту
    map = new ymaps.Map("map", {
        center: [61.7849, 34.3469], 
        zoom: 12,
        controls: ['zoomControl', 'fullscreenControl']
    });

    // 2. Загружаем данные с контроллера
    allEventsFromServer = await loadEventsFromBackend();

    // 3. Показываем все события на карте
    renderMarkers(allEventsFromServer);

    // 4. Показываем сводку дня
    loadDailySummary();
}

// Функция запроса к FastAPI
async function loadEventsFromBackend() {
    try {
        // Меняйте URL на ваш, если порт или хост отличаются
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/events/map?limit=1000`); 
        if (!response.ok) throw new Error('Ошибка сети');
        
        const json = await response.json();
        return json.data; // Возвращаем массив из {"data": result}
    } catch (error) {
        console.error("Не удалось загрузить события с бэкенда:", error);
        return []; // Возвращаем пустой массив в случае ошибки, чтобы скрипт не падал
    }
}

// Рендер маркеров
function renderMarkers(data){
    if (!map) return;
    map.geoObjects.removeAll();
    const coordinateUsage = new Map();

    data.forEach(event => {
        // Пропускаем, если категория не выбрана
        if(selectedCategories.length > 0 && !selectedCategories.includes(event.category)){
            return;
        }

        // Поддерживаем разные варианты координат из бэкенда
        let lat = null, lon = null;
        if (event.geodata && Array.isArray(event.geodata.coordinates) && event.geodata.coordinates.length >= 2){
            lat = event.geodata.coordinates[0];
            lon = event.geodata.coordinates[1];
        } else if (event.coordinates && (event.coordinates.lat || event.coordinates.lon)){
            lat = event.coordinates.lat;
            lon = event.coordinates.lon || event.coordinates.lon;
        } else if (event.lat && event.lng){
            lat = event.lat; lon = event.lng;
        } else if (event.lat && event.lon){
            lat = event.lat; lon = event.lon;
        } else if (event.coords && Array.isArray(event.coords)){
            lat = event.coords[0]; lon = event.coords[1];
        }

        if (lat == null || lon == null) return; // пропускаем события без координат

        // If multiple events share the same coordinate, spread markers around the base point.
        const key = `${lat.toFixed(6)}:${lon.toFixed(6)}`;
        const occurrence = coordinateUsage.get(key) || 0;
        coordinateUsage.set(key, occurrence + 1);

        const coords = getSpreadCoordinates(lat, lon, occurrence);

        const placemark = new ymaps.Placemark(
            coords, 
            {
                balloonContent: `
                    <strong>${event.header || event.title || 'Без названия'}</strong>
                    <br>
                    ${event.location || event.place || ''}
                    <br><br>
                    <b>${event.category || 'Без категории'}</b>
                `
            }, 
            { preset: 'islands#redIcon' }
        );
        placemark.events.add('click', () => {
            trackNewsOpen(event._id || event.id || event.newsId, 'feed');
        });
        map.geoObjects.add(placemark);
    });
}

function getSpreadCoordinates(lat, lon, occurrence) {
    if (occurrence === 0) {
        return [lat, lon];
    }

    const pointsPerRing = 8;
    const ring = Math.floor((occurrence - 1) / pointsPerRing) + 1;
    const indexInRing = (occurrence - 1) % pointsPerRing;
    const angle = (Math.PI * 2 * indexInRing) / pointsPerRing;
    const step = 0.00018; // ~20m in latitude
    const radius = step * ring;

    const jitterLat = lat + Math.sin(angle) * radius;
    const jitterLon = lon + Math.cos(angle) * radius;
    return [jitterLat, jitterLon];
}

// Категории
const categoryButtons = document.querySelectorAll('.category-btn');
categoryButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const category = btn.dataset.category;
        btn.classList.toggle('active');

        if(selectedCategories.includes(category)){
            selectedCategories = selectedCategories.filter(c => c !== category);
        } else {
            selectedCategories.push(category);
        }
        applyFilters();
    });
});

// Общая фильтрация (ищет по сохраненному массиву allEventsFromServer)
function applyFilters(){
    const value = '';
    
    const filtered = allEventsFromServer.filter(event => {
        // Безопасно проверяем строки на случай, если на бэке какое-то поле null
        const title = (event.title || '').toLowerCase();
        const location = (event.location || '').toLowerCase();

        const matchesSearch = value === '' || title.includes(value) || location.includes(value);
        const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(event.category);
        
        return matchesSearch && matchesCategory;
    });

    renderMarkers(filtered);
}
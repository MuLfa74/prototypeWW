let map; 
let selectedCategories = []; 
let allEventsFromServer = [];

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

    data.forEach(event => {
        // Пропускаем, если категория не выбрана
        if(selectedCategories.length > 0 && !selectedCategories.includes(event.category)){
            return;
        }

        // ВАЖНО: Подстраиваем координаты под Яндекс.Карты.
        // Если ваш usecase отдает lat и lng раздельно, собираем их в массив [lat, lng].
        // Если он уже отдает массив coords, замените на: const coords = event.coords;
        const coords = [event.lat, event.lng]; 

        const placemark = new ymaps.Placemark(
            coords, 
            {
                // Заменили event.header и event.annotation на ваши ключи из FastAPI (title/location)
                balloonContent: `
                    <strong>${event.title || 'Без названия'}</strong>
                    <br>
                    ${event.location || ''}
                    <br><br>
                    <b>${event.category || 'Без категории'}</b>
                `
            }, 
            { preset: 'islands#redIcon' }
        );
        map.geoObjects.add(placemark);
    });
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

// Поиск
const searchInput = document.getElementById('search-input');
searchInput.addEventListener('input', () => {
    applyFilters();
});

// Общая фильтрация (ищет по сохраненному массиву allEventsFromServer)
function applyFilters(){
    const value = searchInput.value.toLowerCase();
    
    const filtered = allEventsFromServer.filter(event => {
        // Безопасно проверяем строки на случай, если на бэке какое-то поле null
        const title = (event.title || '').toLowerCase();
        const location = (event.location || '').toLowerCase();

        const matchesSearch = title.includes(value) || location.includes(value);
        const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(event.category);
        
        return matchesSearch && matchesCategory;
    });

    renderMarkers(filtered);
}
import { renderFeed } from './render_news.js';

// Переменная для хранения текущей выбранной категории
let currentCategory = "";

// Находим элементы на странице
const searchInput = document.getElementById('search-input');
const feedContainer = document.getElementById('feed');
const categoryButtons = document.querySelectorAll('.category-btn');

// Главная функция запроса к FastAPI
async function loadEvents() {
  const queryText = searchInput.value.trim();
  let url = `${CONFIG.API_BASE_URL}/api/events/search?`;

  // Формируем Query-параметры для контроллера
  const params = new URLSearchParams();
  if (queryText) params.append('q', queryText);
  if (currentCategory) params.append('category', currentCategory);

  try {
    const response = await fetch(url + params.toString());
    const json = await response.json();
    renderFeed(json.data);
  } catch (error) {
    console.error("Ошибка при получении данных с сервера:", error);
    feedContainer.innerHTML = '<div class="error-msg">Ошибка загрузки новостей</div>';
  }
}

// --- НАВЕШИВАНИЕ СОБЫТИЙ (СЛУШАТЕЛИ) ---

// 1. Поиск при нажатии Enter в инпуте
searchInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    loadEvents();
  }
});

// 2. Фильтрация при клике по категориям в боковой панели
categoryButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const selected = btn.getAttribute('data-category');
    
    // Если кликнули по уже активной категории — сбрасываем фильтр
    if (currentCategory === selected) {
      currentCategory = "";
      btn.classList.remove('active');
    } else {
      // Снимаем класс активности с прошлых кнопок и даем текущей
      categoryButtons.forEach(b => b.classList.remove('active'));
      currentCategory = selected;
      btn.classList.add('active');
    }
    
    // Перезапускаем поиск с учетом выбранной категории
    loadEvents();
  });
});

// ПЕРВОНАЧАЛЬНЫЙ ВЫЗОВ: Загрузка всех новостей при открытии страницы
document.addEventListener('DOMContentLoaded', loadEvents);
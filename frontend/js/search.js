// Переменные и логика инициализируются после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
  let currentCategory = "";

  const searchInput = document.getElementById('search-input');
  const feedContainer = document.getElementById('feed');
  const categoryButtons = document.querySelectorAll('.category-btn');

  if (!searchInput || !feedContainer) return;

  async function loadEvents() {
    const queryText = (searchInput.value || '').trim();
    let url = `${CONFIG.API_BASE_URL}/api/events/search?`;

    const params = new URLSearchParams();
    if (queryText) params.append('q', queryText);
    if (currentCategory) params.append('category', currentCategory);

    try {
      const response = await fetch(url + params.toString());
      const json = await response.json();
      // backend returns { data: [...] } or { data: { content: [...] } }
      renderFeed(json.data);
    } catch (error) {
      console.error("Ошибка при получении данных с сервера:", error);
      feedContainer.innerHTML = '<div class="error-msg">Ошибка загрузки новостей</div>';
    }
  }

  // Поиск при нажатии Enter
  searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') loadEvents();
  });

  // Категории
  categoryButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const selected = btn.getAttribute('data-category');
      if (currentCategory === selected) {
        currentCategory = "";
        btn.classList.remove('active');
      } else {
        categoryButtons.forEach(b => b.classList.remove('active'));
        currentCategory = selected;
        btn.classList.add('active');
      }
      loadEvents();
    });
  });

  // Initial load
  loadEvents();
});
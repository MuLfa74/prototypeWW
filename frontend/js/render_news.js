// Заглушка
function renderFeed(data){
    const container = document.getElementById('feed');

    // Проходим циклом по массиву content
    data.content.forEach(item => {
        // Создаем блок для одной новости
        const eventItem = document.createElement('div');
        eventItem.className = 'event';

        // Формируем внутренний HTML (только заголовок и аннотация)
        eventItem.innerHTML = `
            <h2>${item.header}</h2>
            <div class="annotation">${item.annotation}</div>
            <div class="full-article">${item.content}</div>
        `;

        // НЕ ЗЫБЫТЬ ДОБАВИТЬ СТАТИСТИКУ
        eventItem.addEventListener('click', () => {
            const contentBlock = eventItem.querySelector('.full-article');
            const annotationBlock = eventItem.querySelector('.annotation');
            // toggle переключает класс: если его нет — добавляет, если есть — удаляет
            contentBlock.classList.toggle('show');
            annotationBlock.classList.toggle('show');
        });
    // Добавляем готовую новость в контейнер
    container.appendChild(eventItem);
    });
}
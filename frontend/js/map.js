// Данные событий
const events = [

    {
        id: 1,
        header: "ДТП на перекрестке",
        annotation: "Столкновение двух автомобилей.",
        category: "ДТП",
        date: "23.05.2026",
        coords: [61.7849, 34.3469]
    },

    {
        id: 2,
        header: "Открытие выставки",
        annotation: "В музее открылась новая выставка.",
        category: "Культура",
        date: "23.05.2026",
        coords: [61.7810, 34.3590]
    },

    {
        id: 3,
        header: "Пожар в районе",
        annotation: "Пожарные ликвидировали возгорание.",
        category: "Происшествия",
        date: "22.05.2026",
        coords: [61.7900, 34.3700]
    },

    {
        id: 4,
        header: "Городское мероприятие",
        annotation: "На площади прошло общественное мероприятие.",
        category: "Общество",
        date: "21.05.2026",
        coords: [61.7750, 34.3400]
    }

];

let map;

// Массив выбранных категорий
let selectedCategories = [];

// INIT MAP
ymaps.ready(init);

function init(){

    map = new ymaps.Map("map", {

        center: [61.7849, 34.3469],

        zoom: 12,

        controls: [
            'zoomControl',
            'fullscreenControl'
        ]

    });

    // Показываем все события
    renderMarkers(events);
}

// Рендер маркеров
function renderMarkers(data){

    map.geoObjects.removeAll();

    data.forEach(event => {

        // Если есть выбранные категории
        // и текущая не входит — пропускаем
        if(
            selectedCategories.length > 0 &&
            !selectedCategories.includes(event.category)
        ){
            return;
        }

        const placemark = new ymaps.Placemark(

            event.coords,

            {
                balloonContent: `

                    <strong>
                        ${event.header}
                    </strong>

                    <br>

                    ${event.annotation}

                    <br><br>

                    <b>${event.category}</b>

                `
            },

            {
                preset: 'islands#redIcon'
            }

        );

        map.geoObjects.add(placemark);

    });

}

// Категории
const categoryButtons = document.querySelectorAll('.category-btn');

categoryButtons.forEach(btn => {

    btn.addEventListener('click', () => {

        const category = btn.dataset.category;

        // Toggle active
        btn.classList.toggle('active');

        // Если категория уже есть — удалить
        if(selectedCategories.includes(category)){

            selectedCategories =
                selectedCategories.filter(
                    c => c !== category
                );

        } else {

            selectedCategories.push(category);

        }

        applyFilters();

    });

});

// Поиск
const searchInput =
    document.getElementById('search-input');

searchInput.addEventListener('input', () => {

    applyFilters();

});

// Общая фильтрация
function applyFilters(){

    const value =
        searchInput.value.toLowerCase();

    const filtered = events.filter(event => {

        const matchesSearch =

            event.header
                .toLowerCase()
                .includes(value)

            ||

            event.annotation
                .toLowerCase()
                .includes(value);

        const matchesCategory =

            selectedCategories.length === 0

            ||

            selectedCategories.includes(
                event.category
            );

        return (
            matchesSearch &&
            matchesCategory
        );

    });

    renderMarkers(filtered);

}
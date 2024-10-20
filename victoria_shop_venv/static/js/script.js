document.addEventListener('DOMContentLoaded', function () {
    // Убедитесь, что у каждой формы уникальный ID
    const filterFormCountries = document.getElementById('filterFormCountries'); // Форма для стран
    const filterFormCategories = document.getElementById('filterFormCategories'); // Форма для категорий
    const toggleFilterButton = document.getElementById('toggleFilterMenu');
    const goodsContainer = document.getElementById('goodsContainer');

    // Функция для обновления товаров на странице
    function updateGoods(goods) {
        goodsContainer.innerHTML = ''; // Очистить контейнер с товарами

        if (goods.length === 0) {
            goodsContainer.innerHTML = '<p>Щось пусто :( 😿</p>';
            return;
        }

        goods.forEach(good => {
            const card = document.createElement('div');
            card.classList.add('card');
            card.innerHTML = `
                <div class="image__item">
                    <a href="/description/${good.article}">
                        <img src="data:image/png;base64,${good.base64_data}" alt="${good.name}">
                    </a>
                </div>
                <div class="btn__add__wrapper">
                    <div class="btn__add"></div>
                </div>
                <div class="cost__description">
                    <p class="cost">₴ ${good.price}</p>
                    <p class="description">${good.name}</p>
                </div>
            `;
            goodsContainer.appendChild(card);
        });
    }

    // Функция для отправки запроса с фильтрами и обновления товаров
    function updateFilters() {
        // Собираем данные из обеих форм
        const params = new URLSearchParams(new FormData(filterFormCountries));
        const paramsCategories = new URLSearchParams(new FormData(filterFormCategories));

        // Объединяем параметры из обеих форм
        for (const [key, value] of paramsCategories) {
            params.append(key, value);
        }

        console.log('Отправка фильтров:', params.toString()); // Для отладки

        fetch(`${window.location.pathname}?${params.toString()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Ошибка сети: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Полученные данные:', data); // Для отладки
            updateGoods(data.goods);
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
    }

    // Обработчик для переключения меню фильтров
    toggleFilterButton.addEventListener('click', function () {
        const filterMenu = document.getElementById('filterMenu');
        filterMenu.classList.toggle('active');
    });

    // Запуск фильтрации при изменении чекбоксов
    const checkboxesCountries = filterFormCountries.querySelectorAll('input[type="checkbox"]');
    const checkboxesCategories = filterFormCategories.querySelectorAll('input[type="checkbox"]');

    checkboxesCountries.forEach(checkbox => {
        checkbox.addEventListener('change', updateFilters);
    });

    checkboxesCategories.forEach(checkbox => {
        checkbox.addEventListener('change', updateFilters);
    });
});
"""
Утилиты для определения геолокации по тексту новости
"""
import re
import json
import os

# Определяем путь к файлу относительно текущего скрипта
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DISTRICTS_FILE = os.path.join(CURRENT_DIR, 'petrozavodsk_districts.json')

# Загружаем данные о районах и улицах Петрозаводска
try:
    with open(DISTRICTS_FILE, 'r', encoding='utf-8') as f:
        DISTRICTS_DATA = json.load(f)
    print(f"✅ Загружен файл с районами: {DISTRICTS_FILE}")
except FileNotFoundError:
    print(f"❌ Файл не найден: {DISTRICTS_FILE}")
    print(f"   Текущая директория: {CURRENT_DIR}")
    print(f"   Файлы в директории: {os.listdir(CURRENT_DIR)}")
    DISTRICTS_DATA = {"districts": []}

# Создаем словарь улиц с координатами районов
# Координаты хранятся в формате [latitude, longitude] (широта, долгота)
STREET_TO_COORDINATES = {}
for district in DISTRICTS_DATA.get('districts', []):
    # Меняем порядок: сначала latitude (широта), потом longitude (долгота)
    coordinates = [district['coordinates']['lat'], district['coordinates']['lon']]
    for street in district.get('streets', []):
        STREET_TO_COORDINATES[street.lower()] = coordinates
    
    # Также добавляем название района
    STREET_TO_COORDINATES[district['name'].lower()] = coordinates

def extract_location_from_text(text):
    """
    Извлекает упоминание улицы или района из текста
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Ищем улицы из нашего словаря
    for street in STREET_TO_COORDINATES.keys():
        if street in text_lower:
            return street
    
    # Ищем по шаблонам "на улице X", "в районе Y" и т.д.
    patterns = [
        r'на улице\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$|\s+в|\s+котором)',
        r'на ул\.\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$|\s+в|\s+котором)',
        r'в районе\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$)',
        r'в микрорайоне\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$)',
        r'на проспекте\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$)',
        r'на пр\.\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$)',
        r'на набережной\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$)',
        r'на шоссе\s+([А-Яа-яё\s-]+?)(?:,|\.|\!|\?|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            location = match.group(1).strip()
            # Проверяем, есть ли такая улица/район в словаре
            if location in STREET_TO_COORDINATES:
                return location
    
    return None

def get_coordinates_by_location(location):
    """
    Возвращает координаты по названию улицы или района
    Возвращает [latitude, longitude] (широта, долгота)
    """
    if not location:
        return None
    
    location_lower = location.lower()
    
    if location_lower in STREET_TO_COORDINATES:
        return STREET_TO_COORDINATES[location_lower]
    
    return None

def extract_geodata_from_text(text, title=""):
    """
    Извлекает геоданные из текста новости
    Возвращает coordinates в формате [latitude, longitude]
    """
    # Объединяем заголовок и текст для поиска
    search_text = (title + " " + text).lower()
    
    # Ищем локацию
    location = extract_location_from_text(search_text)
    
    if location:
        coordinates = get_coordinates_by_location(location)
        if coordinates:
            return {
                "type": "Point",
                "coordinates": coordinates  # [latitude, longitude]
            }
    
    return None

def print_geodata_usage_stats(news_list):
    """
    Выводит статистику использования геоданных
    """
    total_news = len(news_list)
    news_with_geodata = sum(1 for news in news_list if news.get('geodata'))
    
    if total_news > 0:
        percentage = (news_with_geodata / total_news) * 100
        print(f"\n📍 ГЕОЛОКАЦИЯ:")
        print(f"  - Новостей с геоданными: {news_with_geodata} из {total_news} ({percentage:.1f}%)")
        
        # Показываем примеры координат
        if news_with_geodata > 0:
            print(f"  - Пример координат: [широта, долгота]")
            for news in news_list[:3]:
                if news.get('geodata'):
                    coords = news['geodata']['coordinates']
                    print(f"    • {coords[0]:.6f}, {coords[1]:.6f}")
    else:
        print(f"\n📍 ГЕОЛОКАЦИЯ:")
        print(f"  - Нет новостей для анализа")
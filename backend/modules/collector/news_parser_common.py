"""
Общие функции для парсинга новостных сайтов
"""
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Конфигурация категорий
CATEGORIES_CONFIG = {
    "categories": [
        {
            "code": "culture",
            "name": "Культура",
            "keywords": ["музей", "экспонат", "произведение", "выставка", "концерт", 
                        "театр", "кино", "фестиваль", "картина", "скульптура", 
                        "артист", "актер", "песня", "танец", "литература"]
        },
        {
            "code": "incident",
            "name": "Происшествия",
            "keywords": ["пожар", "убийство", "взрыв", "теракт", "стрельба", 
                        "нападение", "ограбление", "преступление", "криминал", 
                        "погиб", "погибли", "смерть", "умер", "жертва", "трагедия",
                        "избил", "насилие", "арестовали", "убил", "труп"]
        },
        {
            "code": "traffic accident",
            "name": "ДТП",
            "keywords": ["авария", "пробка", "машина", "ДТП", "столкновение", 
                        "наезд", "водитель", "пешеход", "дорога", "трасса", 
                        "автомобиль", "скорая", "ГИБДД", "авто", "транспорт",
                        "вылетел", "кювет", "перевернулась"]
        },
        {
            "code": "social",
            "name": "Общественная жизнь",
            "keywords": ["стройка", "спасли", "житель", "акция", "митинг", 
                        "собрание", "общество", "волонтер", "помощь", "благоустройство", 
                        "парк", "сквер", "двор", "школа", "больница", "чиновник", 
                        "власть", "выборы", "голосование", "федеральный", "депутат",
                        "жители", "двор", "стройка", "ремонт", "открытие"]
        }
    ]
}

def get_user_agent():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def categorize_news(title, content):
    """Определяет категорию новости на основе заголовка и текста"""
    text_for_search = (title + " " + content).lower()
    category_scores = {}
    
    for category in CATEGORIES_CONFIG["categories"]:
        score = 0
        matched_keywords = []
        
        for keyword in category["keywords"]:
            keyword_lower = keyword.lower()
            if keyword_lower in text_for_search:
                count = text_for_search.count(keyword_lower)
                score += count
                if count > 0 and keyword_lower not in matched_keywords:
                    matched_keywords.append(keyword_lower)
        
        category_scores[category["code"]] = {
            "name": category["name"],
            "score": score,
            "matched_keywords": matched_keywords
        }
    
    best_category = max(category_scores.items(), key=lambda x: x[1]["score"])
    
    if best_category[1]["score"] == 0:
        return {
            "code": "social",
            "name": "Общественная жизнь",
            "confidence": 0
        }
    
    return {
        "code": best_category[0],
        "name": best_category[1]["name"],
        "confidence": best_category[1]["score"]
    }

def trim_to_sentence(text, min_len=600, max_len=700):
    """Обрезает текст до длины между min_len и max_len, заканчивая на границе предложения"""
    if len(text) <= max_len:
        return text
    
    for cut_pos in range(min_len, max_len + 1):
        if cut_pos >= len(text):
            return text
        
        if cut_pos < len(text) and text[cut_pos] in '.!?':
            next_pos = cut_pos + 1
            if next_pos >= len(text) or text[next_pos] in ' \n\r\t"\'»':
                return text[:cut_pos + 1]
        
        for offset in [1, 2]:
            check_pos = cut_pos - offset
            if check_pos > min_len and text[check_pos] in '.!?':
                next_after_check = check_pos + 1
                if next_after_check >= len(text) or text[next_after_check] in ' \n\r\t"\'»':
                    return text[:check_pos + 1]
    
    last_punct = max(text.rfind('.', min_len, max_len),
                     text.rfind('!', min_len, max_len),
                     text.rfind('?', min_len, max_len))
    
    if last_punct > min_len:
        return text[:last_punct + 1]
    else:
        return text[:max_len] + "..."

def clean_text(text):
    """Очищает текст от лишних пробелов и специальных символов"""
    text = re.sub(r'\s+', ' ', text)
    remove_phrases = [
        r'Наш сайт использует файлы cookies.*',
        r'Подробнее здесь.*',
        r'Политика конфиденциальности.*',
        r'©.*',
        r'Все права защищены.*',
        r'Фото.*',
        r'Видео.*',
        r'Источник:.*',
        r'Читайте также.*'
    ]
    for phrase in remove_phrases:
        text = re.sub(phrase, '', text, flags=re.IGNORECASE)
    return text.strip()

def create_annotation(content, max_len=200):
    """
    Создает краткое описание (аннотацию) из текста новости
    
    Args:
        content (str): Полный текст новости
        max_len (int): Максимальная длина аннотации
    
    Returns:
        str: Краткое описание
    """
    if not content:
        return ""
    
    # Берем первое предложение
    sentences = re.split(r'[.!?]', content)
    if sentences and sentences[0]:
        annotation = sentences[0].strip()
        if len(annotation) > max_len:
            annotation = annotation[:max_len] + "..."
        return annotation
    
    # Если не получилось, берем начало текста
    return content[:max_len].strip() + "..."

def save_all_to_json(all_news, filename='all_news.json'):
    """Сохраняет все новости в один JSON файл в нужном формате"""
    clean_news_list = []
    for news in all_news:
        clean_news = {
            "header": news.get('title', ''),
            "content": news.get('content', news.get('text', '')),
            "annotation": create_annotation(news.get('content', news.get('text', '')), 200),
            "category": news['category']['name'],
            "date": news.get('date', ''),
            "source": news.get('source', ''),
            "link": news.get('link', '')
        }
        
        # Добавляем геоданные, если есть (без location_name)
        if 'geodata' in news and news['geodata']:
            clean_news['geodata'] = news['geodata']
        else:
            clean_news['geodata'] = None
        
        clean_news_list.append(clean_news)
    
    output = {
        "metadata": {
            "total_news": len(clean_news_list),
            "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": list(set(news['source'] for news in clean_news_list))
        },
        "news": clean_news_list
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Все новости сохранены в файл: {filename}")
    print(f"   Всего новостей: {len(clean_news_list)}")

def print_category_statistics(all_news):
    """Выводит статистику по категориям в консоль"""
    print("\n" + "="*60)
    print("📊 СТАТИСТИКА ПО КАТЕГОРИЯМ")
    print("="*60)
    
    category_counts = {}
    source_counts = {}
    
    for news in all_news:
        cat_name = news['category']['name']
        source = news.get('source', 'unknown')
        category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print("\nПо категориям:")
    for cat_name, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(all_news)) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {cat_name:20} {count:2} новостей ({percentage:5.1f}%) {bar}")
    
    print("\nПо источникам:")
    for source, count in sorted(source_counts.items()):
        percentage = (count / len(all_news)) * 100
        print(f"  {source:20} {count:2} новостей ({percentage:5.1f}%)")
    
    print("="*60)
"""
Парсер для VK сообществ
"""
import vk_api
import re
from datetime import datetime
from dotenv import load_dotenv
import os
from news_parser_common import categorize_news, trim_to_sentence

# Загружаем переменные окружения
load_dotenv()

# Конфигурация сообществ
VK_GROUPS = {
    "dtpptz": {
        "domain": "dtpptz",
        "default_category": "traffic accident",  # Всегда ДТП
        "category_name": "ДТП"
    },
    "petrozavodsklive": {
        "domain": "petrozavodsklive",
        "default_category": None,  # Определяем по тексту
        "category_name": None
    },
    "nashakarelia": {
        "domain": "nashakarelia",
        "default_category": None,  # Определяем по тексту
        "category_name": None
    }
}

def get_first_sentence(text):
    """
    Извлекает первое предложение из текста до точки или переноса строки
    
    Args:
        text (str): Исходный текст
    
    Returns:
        str: Первое предложение до точки или \n
    """
    if not text:
        return "Без заголовка"
    
    # Ищем позицию первой точки или переноса строки
    dot_pos = text.find('.')
    newline_pos = text.find('\n')
    
    # Определяем самую раннюю позицию
    end_pos = len(text)
    if dot_pos != -1 and dot_pos < end_pos:
        end_pos = dot_pos
    if newline_pos != -1 and newline_pos < end_pos:
        end_pos = newline_pos
    
    # Если нашли точку или перенос строки
    if end_pos < len(text):
        title = text[:end_pos + 1].strip()  # +1 чтобы включить точку
    else:
        # Если нет ни точки, ни переноса строки, берем первые 150 символов
        title = text[:150].strip()
    
    # Если заголовок слишком короткий (меньше 10 символов), берем немного больше
    if len(title) < 10 and len(text) > 50:
        title = text[:100].strip()
    
    # Ограничиваем максимальную длину
    if len(title) > 200:
        title = title[:197] + "..."
    
    return title

def get_wall_posts(domain, offset=0, count=5):
    """
    Получает посты из стены ВК
    
    Args:
        domain (str): домен сообщества
        offset (int): сдвиг (сколько постов пропустить)
        count (int): количество постов для получения
    
    Returns:
        list: список обработанных постов в едином формате
    """
    try:
        access_token = os.getenv("access_token")
        app_id = os.getenv("app_id")
        app_secret = os.getenv("app_secret")
        
        if not access_token:
            print(f"  ❌ Ошибка: Не найден access_token в .env файле")
            return []
        
        vk_session = vk_api.VkApi(token=access_token, app_id=app_id, client_secret=app_secret)
        vk = vk_session.get_api()
        
        # Получаем посты
        json_wall = vk.wall.get(domain=domain, offset=offset, count=count)
        
        processed_posts = []
        
        for post in json_wall["items"]:
            # Извлекаем текст поста
            post_text = post.get("text", "")
            
            if not post_text:
                continue  # Пропускаем пустые посты
            
            # Создаем заголовок из первого предложения
            title = get_first_sentence(post_text)
            
            # Получаем дату
            post_date = datetime.fromtimestamp(post.get("date", 0)).strftime("%d.%m.%Y %H:%M")
            
            # Получаем geo координаты (если есть)
            geo = None
            if "geo" in post and post["geo"]:
                geo = post["geo"].get("coordinates", None)
            
            # Ссылка на пост
            post_link = f"https://vk.com/wall{post['owner_id']}_{post['id']}"
            
            # Определяем категорию
            group_config = VK_GROUPS.get(domain, {})
            default_category = group_config.get("default_category")
            
            if default_category == "traffic accident":
                # Для dtpptz всегда ставим категорию ДТП
                category_info = {
                    "code": "traffic accident",
                    "name": "ДТП",
                    "confidence": 100,  # Максимальная уверенность
                    "matched_keywords": ["dtpptz - паблик ДТП"]
                }
            else:
                # Для других пабликов определяем по тексту
                category_info = categorize_news(title, post_text)
            
            # Обрезаем текст до 600-700 символов
            trimmed_text = trim_to_sentence(post_text, min_len=600, max_len=700)
            
            processed_posts.append({
                'source': f'vk.com/{domain}',
                'title': title,
                'date': post_date,
                'link': post_link,
                'text': trimmed_text,
                'geo': geo,  # Координаты (если есть)
                'category': {
                    'code': category_info['code'],
                    'name': category_info['name'],
                    'confidence': category_info['confidence']
                }
            })
        
        return processed_posts
    
    except Exception as e:
        print(f"  ❌ Ошибка при парсинге VK (domain={domain}): {e}")
        return []

def parse_all_vk_groups(max_posts_per_group=5):
    """
    Парсит все настроенные VK сообщества
    
    Args:
        max_posts_per_group (int): Максимум постов с каждого сообщества
    
    Returns:
        list: Список всех постов со всех сообществ
    """
    all_posts = []
    
    for group_key, group_config in VK_GROUPS.items():
        domain = group_config["domain"]
        print(f"\n📱 Парсинг VK: {domain}")
        
        posts = get_wall_posts(domain=domain, offset=0, count=max_posts_per_group)
        
        if posts:
            print(f"  ✅ Получено {len(posts)} постов")
            all_posts.extend(posts)
        else:
            print(f"  ⚠️ Не удалось получить посты")
    
    return all_posts

# Для тестирования (если запускаешь этот файл напрямую)
if __name__ == "__main__":
    print("="*60)
    print("🚀 ТЕСТИРОВАНИЕ VK ПАРСЕРА")
    print("="*60)
    
    posts = parse_all_vk_groups(max_posts_per_group=3)
    
    for post in posts:
        print(f"\n📱 Источник: {post['source']}")
        print(f"📌 Заголовок: {post['title']}")
        print(f"📅 Дата: {post['date']}")
        print(f"🏷️ Категория: {post['category']['name']}")
        if post['geo']:
            print(f"📍 Координаты: {post['geo']}")
        print(f"📝 Текст: {post['text'][:150]}...")
        print(f"🔗 Ссылка: {post['link']}")
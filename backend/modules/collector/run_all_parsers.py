"""
Запуск всех парсеров новостей (сайты + VK) с определением геолокации
и сохранением в MongoDB
"""
import sys
import os
from datetime import datetime

# Добавляем путь к папке backend (где лежит db.py)
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print(f"🔍 Путь к backend: {backend_path}")
print(f"🔍 Содержимое sys.path: {sys.path[:3]}")

try:
    from db import connect, get_mongo_collection, close
    print("✅ Модуль db успешно импортирован")
except ModuleNotFoundError as e:
    print(f"❌ Ошибка импорта db: {e}")
    print(f"   Проверьте, что файл существует: {os.path.join(backend_path, 'db.py')}")
    print(f"   Файл существует: {os.path.exists(os.path.join(backend_path, 'db.py'))}")
    sys.exit(1)

from news_parser_common import save_all_to_json, print_category_statistics
from geolocation_utils import extract_geodata_from_text, print_geodata_usage_stats

# Импортируем парсеры
from parser_factornews import parse_factornews
from parser_gubdaily import parse_gubdaily
from parser_vk import parse_all_vk_groups

def save_to_mongodb(all_news, collection_name=None):
    """
    Сохраняет новости в MongoDB
    
    Args:
        all_news (list): Список новостей
        collection_name (str): Имя коллекции (опционально)
    
    Returns:
        int: Количество сохраненных документов
    """
    if not all_news:
        print("⚠️ Нет новостей для сохранения в MongoDB")
        return 0
    
    try:
        # Подключаемся к MongoDB
        collection = get_mongo_collection(collection_name)
        
        # Подготавливаем документы для вставки
        documents = []
        for news in all_news:
            doc = {
                "header": news.get('title', ''),
                "content": news.get('content', news.get('text', '')),
                "annotation": create_annotation(news.get('content', news.get('text', '')), 200),
                "category": news['category']['name'],
                "date": news.get('date', ''),
                "source": news.get('source', ''),
                "link": news.get('link', ''),
                "parsed_at": datetime.now(),
                "geodata": news.get('geodata')
            }
            documents.append(doc)
        
        # Вставка в MongoDB
        if documents:
            result = collection.insert_many(documents)
            print(f"\n✅ Сохранено в MongoDB: {len(result.inserted_ids)} документов")
            return len(result.inserted_ids)
        else:
            return 0
            
    except Exception as e:
        print(f"\n❌ Ошибка при сохранении в MongoDB: {e}")
        return 0

def create_annotation(content, max_len=200):
    """
    Создает краткое описание (аннотацию) из текста новости
    """
    if not content:
        return ""
    
    # Берем первое предложение
    import re
    sentences = re.split(r'[.!?]', content)
    if sentences and sentences[0]:
        annotation = sentences[0].strip()
        if len(annotation) > max_len:
            annotation = annotation[:max_len] + "..."
        return annotation
    
    # Если не получилось, берем начало текста
    return content[:max_len].strip() + "..."

def run_all_parsers(max_news_per_source=5, include_vk=True, save_to_file=True, save_to_db=True):
    """
    Запускает все парсеры и объединяет результаты с определением геолокации
    
    Args:
        max_news_per_source (int): Максимум новостей с каждого источника
        include_vk (bool): Включать ли VK парсер
        save_to_file (bool): Сохранять ли в JSON файл
        save_to_db (bool): Сохранять ли в MongoDB
    """
    print("="*60)
    print("🚀 ЗАПУСК ВСЕХ ПАРСЕРОВ НОВОСТЕЙ")
    print("="*60)
    print(f"📌 Максимум новостей с каждого источника: {max_news_per_source}")
    if include_vk:
        print("📌 Источники: factornews.ru, gubdaily.ru, VK (dtpptz, petrozavodsklive, nashakarelia)")
    print("📍 Автоматическое определение геолокации по тексту")
    if save_to_db:
        print("💾 Сохранение в MongoDB")
    print("="*60)
    
    all_news = []
    
    # Парсим factornews.ru
    print("\n" + "="*60)
    print("📰 ПАРСЕР 1/3: factornews.ru")
    print("="*60)
    factornews_news = parse_factornews(max_news=max_news_per_source)
    if factornews_news:
        # Добавляем геоданные
        for news in factornews_news:
            geodata = extract_geodata_from_text(news['content'], news['title'])
            news['geodata'] = geodata
        all_news.extend(factornews_news)
        print(f"\n✅ factornews.ru: спарсено {len(factornews_news)} новостей")
    else:
        print("\n⚠️ factornews.ru: не удалось спарсить новости")
    
    # Парсим gubdaily.ru
    print("\n" + "="*60)
    print("📰 ПАРСЕР 2/3: gubdaily.ru")
    print("="*60)
    gubdaily_news = parse_gubdaily(max_news=max_news_per_source)
    if gubdaily_news:
        # Добавляем геоданные
        for news in gubdaily_news:
            geodata = extract_geodata_from_text(news['content'], news['title'])
            news['geodata'] = geodata
        all_news.extend(gubdaily_news)
        print(f"\n✅ gubdaily.ru: спарсено {len(gubdaily_news)} новостей")
    else:
        print("\n⚠️ gubdaily.ru: не удалось спарсить новости")
    
    # Парсим VK
    if include_vk:
        print("\n" + "="*60)
        print("📱 ПАРСЕР 3/3: VK сообщества")
        print("="*60)
        vk_news = parse_all_vk_groups(max_posts_per_group=max_news_per_source)
        if vk_news:
            # Добавляем геоданные
            for news in vk_news:
                geodata = extract_geodata_from_text(news['text'], news['title'])
                news['geodata'] = geodata
                # Переименовываем text в content для единообразия
                news['content'] = news.pop('text')
            all_news.extend(vk_news)
            print(f"\n✅ VK: спарсено {len(vk_news)} постов")
        else:
            print("\n⚠️ VK: не удалось спарсить посты")
    
    if not all_news:
        print("\n❌ Не удалось спарсить новости ни с одного источника")
        return []
    
    print("\n" + "="*60)
    print("📊 ОБЩАЯ СТАТИСТИКА")
    print("="*60)
    print(f"✅ Всего спарсено новостей: {len(all_news)}")
    
    print_category_statistics(all_news)
    print_geodata_usage_stats(all_news)
    
    # Сохраняем в JSON файл
    if save_to_file:
        save_all_to_json(all_news, 'all_news.json')
    
    # Сохраняем в MongoDB
    if save_to_db:
        try:
            # Подключаемся к MongoDB
            connect()
            saved_count = save_to_mongodb(all_news)
            if saved_count > 0:
                print(f"\n💾 Успешно сохранено в MongoDB: {saved_count} документов")
        except Exception as e:
            print(f"\n❌ Ошибка при работе с MongoDB: {e}")
        finally:
            close()
    
    return all_news

def main():
    """Точка входа для однократного запуска"""
    MAX_NEWS_PER_SOURCE = 5
    INCLUDE_VK = True
    SAVE_TO_FILE = True
    SAVE_TO_DB = True
    
    try:
        run_all_parsers(
            max_news_per_source=MAX_NEWS_PER_SOURCE,
            include_vk=INCLUDE_VK,
            save_to_file=SAVE_TO_FILE,
            save_to_db=SAVE_TO_DB
        )
        print("\n✨ Парсинг успешно завершен!")
    except KeyboardInterrupt:
        print("\n\n⚠️ Парсинг прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
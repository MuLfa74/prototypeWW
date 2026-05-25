"""
Запуск всех парсеров новостей (сайты + VK) с определением геолокации
и сохранением в MongoDB
"""
import sys
import os
import json
import traceback
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

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

STATUS_FILE = os.path.join(os.path.dirname(__file__), 'parse_status.json')


def normalize_title(title):
    return ' '.join(str(title or '').split()).strip().lower()


def dedupe_news_by_title(all_news):
    unique_news = []
    seen_titles = set()

    for news in all_news:
        title = news.get('title') or news.get('header') or news.get('link') or ''
        title_key = normalize_title(title)
        if not title_key:
            title_key = normalize_title(news.get('content') or news.get('text') or '')

        if title_key in seen_titles:
            continue

        seen_titles.add(title_key)
        unique_news.append(news)

    return unique_news


def write_parse_status(all_news):
    status = {
        "last_updated": datetime.now().isoformat(timespec='seconds'),
        "news_count": len(all_news),
        "sources": sorted({news.get('source', '') for news in all_news if news.get('source')}),
    }

    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

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
        all_news = dedupe_news_by_title(all_news)

        # Подключаемся к MongoDB
        collection = get_mongo_collection(collection_name)
        
        # Подготавливаем документы для вставки
        documents = []
        for news in all_news:
            header = news.get('title', '').strip()
            header_key = normalize_title(header)
            if not header_key:
                continue

            doc = {
                "header": header,
                "header_key": header_key,
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
            inserted_count = 0
            updated_count = 0
            for doc in documents:
                result = collection.update_one(
                    {"header_key": doc["header_key"]},
                    {"$set": doc, "$setOnInsert": {"created_at": datetime.now()}},
                    upsert=True,
                )
                if result.upserted_id is not None:
                    inserted_count += 1
                else:
                    updated_count += 1

            print(f"\n✅ Сохранено/обновлено в MongoDB: {inserted_count} новых, {updated_count} обновлено")
            return len(documents)
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

    all_news = dedupe_news_by_title(all_news)
    
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
            traceback.print_exc()
        finally:
            close()

    write_parse_status(all_news)
    
    return all_news

def main():
    """Точка входа для однократного запуска"""
    MAX_NEWS_PER_SOURCE = 10
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
"""
Запуск всех парсеров новостей (сайты + VK)
"""
import sys
from news_parser_common import save_all_to_json, print_category_statistics

# Импортируем парсеры
from parser_factornews import parse_factornews
from parser_gubdaily import parse_gubdaily
from parser_vk import parse_all_vk_groups

def run_all_parsers(max_news_per_source=5, include_vk=True, save_to_file=True):
    """
    Запускает все парсеры и объединяет результаты
    
    Args:
        max_news_per_source (int): Максимум новостей с каждого источника
        include_vk (bool): Включать ли VK парсер
        save_to_file (bool): Сохранять ли результат в файл
    
    Returns:
        list: Список всех новостей
    """
    print("="*60)
    print("🚀 ЗАПУСК ВСЕХ ПАРСЕРОВ НОВОСТЕЙ")
    print("="*60)
    print(f"📌 Максимум новостей с каждого источника: {max_news_per_source}")
    if include_vk:
        print("📌 Источники: factornews.ru, gubdaily.ru, VK (dtpptz, petrozavodsklive, nashakarelia)")
    else:
        print("📌 Источники: factornews.ru, gubdaily.ru")
    print("="*60)
    
    all_news = []
    
    # Парсим factornews.ru
    print("\n" + "="*60)
    print("📰 ПАРСЕР 1/3: factornews.ru")
    print("="*60)
    factornews_news = parse_factornews(max_news=max_news_per_source)
    if factornews_news:
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
    
    # Дополнительная статистика по VK geo
    vk_geo_count = sum(1 for news in all_news if news.get('geo'))
    if vk_geo_count > 0:
        print(f"\n📍 VK посты с геолокацией: {vk_geo_count}")
    
    if save_to_file:
        save_all_to_json(all_news, 'all_news.json')
    
    return all_news

def main():
    """Точка входа для однократного запуска"""
    MAX_NEWS_PER_SOURCE = 5
    INCLUDE_VK = True  # Меняй на False, если не нужно парсить VK
    
    try:
        run_all_parsers(
            max_news_per_source=MAX_NEWS_PER_SOURCE,
            include_vk=INCLUDE_VK,
            save_to_file=True
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
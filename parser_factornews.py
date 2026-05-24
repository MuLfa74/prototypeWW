"""
Парсер для factornews.ru
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
from news_parser_common import (
    get_user_agent, categorize_news, clean_text, trim_to_sentence
)

def parse_news_content(url):
    """
    Переходит по ссылке новости и извлекает текст
    """
    try:
        response = requests.get(url, headers=get_user_agent(), timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ❌ Ошибка при загрузке: {e}")
        return ""
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Ищем контейнер с текстом новости
    news_body = soup.find('div', class_='news__text')
    
    if not news_body:
        news_body = soup.find('article')
    
    if not news_body:
        news_body = soup.find('div', class_='content')
    
    if not news_body:
        return "Текст новости не найден"
    
    # Очищаем от скриптов и стилей
    for bad in news_body.find_all(['script', 'style', 'noscript']):
        bad.decompose()
    
    # Удаляем изображения и видео (только текст)
    for img in news_body.find_all(['img', 'figure', 'video', 'iframe']):
        img.decompose()
    
    # Получаем текст
    full_text = news_body.get_text(separator=' ', strip=True)
    full_text = clean_text(full_text)
    
    if not full_text or len(full_text) < 50:
        return full_text if full_text else "Текст новости не найден"
    
    return trim_to_sentence(full_text, min_len=600, max_len=700)

def parse_factornews(max_news=5):
    """
    Парсер главной страницы factornews.ru
    """
    base_url = 'https://factornews.ru'
    news_url = urljoin(base_url, '/news/')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(news_url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Ошибка при загрузке главной страницы factornews.ru: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Ищем все блоки с заголовками
    news_cards = soup.find_all('div', class_='main__card-f-title')
    
    if not news_cards:
        print("⚠️ Не найдены блоки с новостями на factornews.ru")
        return []
    
    news_cards = news_cards[:max_news]
    print(f"Найдено {len(news_cards)} новостей на factornews.ru")
    
    all_news = []
    
    for idx, card in enumerate(news_cards, 1):
        try:
            link_tag = card.find('a')
            if not link_tag:
                continue
                
            title = link_tag.get_text(strip=True)
            relative_link = link_tag.get('href')
            
            if not relative_link or not title:
                continue
                
            full_link = urljoin(base_url, relative_link)
            
            # Ищем дату
            date_value = "Дата не найдена"
            parent = card.parent
            for _ in range(5):
                if parent:
                    date_div = parent.find('div', class_=re.compile(r'tool-value|date', re.I))
                    if date_div:
                        date_value = date_div.get_text(strip=True)
                        break
                    parent = parent.parent
                else:
                    break
            
            print(f"\n[{idx}/{max_news}] factornews.ru: {title[:50]}...")
            news_text = parse_news_content(full_link)
            category_info = categorize_news(title, news_text)
            
            all_news.append({
                'source': 'factornews.ru',
                'title': title,
                'date': date_value,
                'link': full_link,
                'content': news_text,
                'category': {
                    'code': category_info['code'],
                    'name': category_info['name'],
                    'confidence': category_info['confidence']
                }
            })
            
            print(f"  📌 Категория: {category_info['name']}")
            print(f"  📝 Длина текста: {len(news_text)} символов")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            continue
    
    return all_news
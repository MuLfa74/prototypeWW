"""
Парсер для gubdaily.ru
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
    news_body = soup.find('article')
    
    if not news_body:
        news_body = soup.find('div', class_='entry-content')
    
    if not news_body:
        news_body = soup.find('div', class_='post-content')
    
    if not news_body:
        return "Текст новости не найден"
    
    # Очищаем от скриптов и стилей
    for bad in news_body.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        bad.decompose()
    
    # Удаляем изображения и видео
    for img in news_body.find_all(['img', 'figure', 'video', 'iframe']):
        img.decompose()
    
    # Получаем текст
    full_text = news_body.get_text(separator=' ', strip=True)
    full_text = clean_text(full_text)
    
    if not full_text or len(full_text) < 50:
        return full_text if full_text else "Текст новости не найден"
    
    return trim_to_sentence(full_text, min_len=600, max_len=700)

def parse_gubdaily(max_news=5):
    """
    Парсер главной страницы gubdaily.ru
    """
    base_url = 'https://gubdaily.ru'
    
    try:
        response = requests.get(base_url, headers=get_user_agent(), timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Ошибка при загрузке главной страницы gubdaily.ru: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Ищем все новости
    found_news = []
    news_links = soup.find_all('a', href=True)
    
    for link in news_links:
        h2_tag = link.find('h2')
        if h2_tag and link.get('href'):
            title = h2_tag.get_text(strip=True)
            relative_link = link.get('href')
            
            if relative_link.startswith('/'):
                full_link = urljoin(base_url, relative_link)
            elif relative_link.startswith('http'):
                full_link = relative_link
            else:
                continue
            
            if '/news/' in full_link or re.search(r'/\d{4}/\d{2}/', full_link):
                # Ищем дату
                date_value = "Дата не найдена"
                parent = link.parent
                for _ in range(3):
                    if parent:
                        date_span = parent.find('span', class_=re.compile(r'date|pub-date|time', re.I))
                        if date_span:
                            date_value = date_span.get_text(strip=True)
                            break
                        time_elem = parent.find('time')
                        if time_elem:
                            date_value = time_elem.get_text(strip=True)
                            break
                        parent = parent.parent
                    else:
                        break
                
                found_news.append({
                    'title': title,
                    'link': full_link,
                    'date': date_value
                })
    
    # Удаляем дубликаты
    unique_news = []
    seen_links = set()
    for news in found_news:
        if news['link'] not in seen_links:
            seen_links.add(news['link'])
            unique_news.append(news)
    
    unique_news = unique_news[:max_news]
    print(f"Найдено {len(unique_news)} новостей на gubdaily.ru")
    
    parsed_news = []
    
    for idx, news in enumerate(unique_news, 1):
        try:
            print(f"\n[{idx}/{max_news}] gubdaily.ru: {news['title'][:50]}...")
            news_text = parse_news_content(news['link'])
            category_info = categorize_news(news['title'], news_text)
            
            parsed_news.append({
                'source': 'gubdaily.ru',
                'title': news['title'],
                'date': news['date'],
                'link': news['link'],
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
    
    return parsed_news
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
from news_parser_common import get_user_agent, categorize_news, clean_text, trim_to_sentence

def parse_news_content(url):
    try:
        response = requests.get(url, headers=get_user_agent(), timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ❌ Ошибка: {e}")
        return ""
    
    soup = BeautifulSoup(response.text, 'html.parser')
    news_body = soup.find('div', class_='news__text')
    
    if not news_body:
        return "Текст новости не найден"
    
    for bad in news_body.find_all(['script', 'style', 'img', 'figure', 'video']):
        bad.decompose()
    
    full_text = news_body.get_text(separator=' ', strip=True)
    full_text = clean_text(full_text)
    
    if not full_text or len(full_text) < 50:
        return full_text if full_text else "Текст новости не найден"
    
    return trim_to_sentence(full_text, min_len=600, max_len=700)

def parse_factornews(max_news=5):
    base_url = 'https://factornews.ru'
    news_url = urljoin(base_url, '/news/')
    
    try:
        response = requests.get(news_url, headers=get_user_agent(), timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Ошибка загрузки factornews.ru: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    news_cards = soup.find_all('div', class_='main__card-f-title')
    
    if not news_cards:
        print("⚠️ Не найдены новости на factornews.ru")
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
            full_link = urljoin(base_url, relative_link)
            
            # Поиск даты
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
            category_info = categorize_news(title, news
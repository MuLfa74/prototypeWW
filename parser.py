import vk_api
import json
from dotenv import load_dotenv
import os

load_dotenv()

def get_wall_posts(domain, offset, count):
    """
    Получает посты из стены ВК
    
    Args:
        domain (str): домен сообщества
        offset (int): сдвиг (сколько постов пропустить)
        count (int): количество постов для получения
    
    Returns:
        list: список обработанных постов
    """
    try:
        access_token = os.getenv("access_token")
        app_id = os.getenv("app_id")
        app_secret = os.getenv("app_secret")
        
        vk_session = vk_api.VkApi(token=access_token, app_id=app_id, client_secret=app_secret)
        vk = vk_session.get_api()
        
        json_wall = vk.wall.get(domain=domain, offset=offset, count=count)
        with open("test_pars.json", "w") as json_file: 
            json.dump(json_wall, json_file, indent=2, ensure_ascii=True)   # записывает словарь json_wall в json  файл json_file 
        
        processed_posts = []
        
        for inside in json_wall["items"]:
            processed_wall = {}
            
            # Фото
            try:
                processed_wall["post_photo"] = inside["attachments"][1]["photo"]["sizes"][5]["url"]
            except (KeyError, IndexError):
                processed_wall["post_photo"] = None
            
            # Координаты
            try:
                processed_wall["geo"] = inside["geo"]["coordinates"]
            except KeyError:
                processed_wall["geo"] = None
            
            # Текст
            try:
                processed_wall["text"] = inside["text"]
            except KeyError:
                processed_wall["text"] = None
            
            processed_posts.append(processed_wall)
            
        
        return processed_posts
    
    except Exception as e:
        print(f"Ошибка: {e}")
        return []

# Для тестирования (если запускаешь этот файл напрямую)
if __name__ == "__main__":
    posts = get_wall_posts()
    for post in posts:
        print(post)
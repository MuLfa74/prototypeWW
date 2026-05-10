import vk_api
import json
#import tOKENs11
from dotenv import load_dotenv
import os


load_dotenv()  # Загружает из .env  
access_token = os.getenv("access_token")
app_id = os.getenv("app_id")
app_secret = os.getenv("app_secret")

#  токен вместо логина и пароля
#access_token = tOKENs11.access_token - старый импорт без env
try:
    vk_session = vk_api.VkApi(token=access_token, app_id=app_id, client_secret=app_secret)
    vk = vk_session.get_api()
    
    json_wall = vk.wall.get(domain="dtpptz", offset=1, count=1)
    print(json_wall)
  
    with open("test_pars.json", "w") as json_file: 
        json.dump(json_wall, json_file, indent=2, ensure_ascii=True)   # записывает словарь json_wall в json  файл json_file 

        #title = json_wall.get("items").get("attachments")
    """for info in  json_wall.get("items"):
        post_info = {
            "post_blabla" : info.get("attachments")[1].get("photo").get("")
            
        }
        print(post_info.get("post_blabla"))""" #вытягивание инфы
except Exception as e:
    print(f"Ошибка: {e}")
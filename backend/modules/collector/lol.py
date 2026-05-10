import vk_api

    
json_wall = vk.wall.get(domain="dtpptz", offset = 1, count = 2)

print(json_wall)
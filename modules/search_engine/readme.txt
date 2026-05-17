как поднять локально докер:
1. Запустить Elasticsearch через Docker:
 docker run -d --name elastic `
 -p 9200:9200 `
 -e "discovery.type=single-node" `
 -e "xpack.security.enabled=false" `
 -e ES_JAVA_OPTS="-Xms512m -Xmx512m" `
 elasticsearch:8.13.0

2. Создать mapping:
 $body = @{
   mappings = @{
     properties = @{
       header     = @{ type = "text" }
       content    = @{ type = "text" }
       annotation = @{ type = "text" }
       category   = @{ type = "keyword" }
       date       = @{ type = "date" }
       geodata    = @{ type = "geo_point" }
     }
   }
 } | ConvertTo-Json -Depth 5
 Invoke-RestMethod -Method Put `
   -Uri "http://localhost:9200/news" `
   -ContentType "application/json" `
   -Body $body

3. Создать файл с тестовыми данными
Пример файла data.ndjson:
 { "index": {} }
 { "header": "Пожар в центре города", "content": "Сильный пожар произошел ночью...", "annotation": "Пожар в Москве", "category": "incident", "date": "2026-01-12T13:00:00Z", "geodata": { "lat": 55.7558, "lon": 37.6173 } }
 { "index": {} }
 { "header": "Политическая встреча", "content": "Лидеры стран обсудили важные вопросы...", "annotation": "Лидеры стран провели встречу", "category": "politics", "date": "2026-02-01T10:00:00Z", "geodata": { "lat": 59.9343, "lon": 30.3351 } }
 { "index": {} }
 { "header": "Концерт в парке", "content": "Большой концерт под открытым небом...", "annotation": "В парке устраивают концерт", "category": "culture", "date": "2026-03-05T18:00:00Z", "geodata": { "lat": 50.4501, "lon": 30.5234 } }

4. Внести данные в Elasticsearch:
 Invoke-RestMethod -Method Post `
   -Uri "http://localhost:9200/news/_bulk" `
   -ContentType "application/x-ndjson" `
   -InFile "C:\Users\TurboPC\Desktop\search\data.ndjson"

  Если нужно удалить из эластика:
  Invoke-RestMethod -Method Delete `
    -Uri "http://localhost:9200/news"

5. Подключение к Elasticsearch в search.py:
 Elasticsearch("http://localhost:9200")
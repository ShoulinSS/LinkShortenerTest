# Микросервис для сокращения ссылок (тестовое задание)

Команды докера для сборки и тестирования проекта:
`docker-compose up --build -d` -d для удобного запуска unit-тестов.

`docker-compose exec web pytest unit-tests.py -v` - запускает unit-тесты.



Принимает json формата {url: url} и возвращает json формата {short_id: id} по эндпоинту POST/shorten.

Перенаправляет на оригинальную ссылку по эндпоинту GET/{short_id}.

Возвращает json формата {short_id: id, usage_count: count} по эндопинту GET/stats/{short_id}.

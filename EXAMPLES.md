# 📚 Примеры использования модулей

Этот документ содержит примеры использования функций из различных модулей проекта для разработчиков.

## 🔌 mysql_connector.py

### Поиск фильмов по ключевому слову

```python
from mysql_connector import search_by_keyword

# Простой поиск
films = search_by_keyword("matrix", offset=0, limit=10)

# Поиск с фильтром по жанру
films = search_by_keyword("love", genre_id=7, offset=0, limit=10)

# Поиск с фильтром по годам и рейтингу
films = search_by_keyword(
    "action",
    genre_id=1,
    year_min=2005,
    year_max=2010,
    rating="PG-13",
    offset=0,
    limit=10
)
```

### Поиск фильмов по жанру и диапазону лет

```python
from mysql_connector import search_by_genre_and_year

# Поиск по жанру и годам
films = search_by_genre_and_year(
    genre_id=1,
    year_min=2005,
    year_max=2010,
    offset=0,
    limit=10
)

# С фильтром по рейтингу
films = search_by_genre_and_year(
    genre_id=1,
    year_min=2005,
    year_max=2010,
    rating="PG",
    offset=0,
    limit=10
)
```

### Получение списка жанров

```python
from mysql_connector import get_genres

genres = get_genres()
for genre in genres:
    print(f"{genre['category_id']}: {genre['name']}")
```

### Получение диапазона годов

```python
from mysql_connector import get_year_bounds

min_year, max_year = get_year_bounds()
print(f"Фильмы с {min_year} по {max_year} год")
```

### Подсчёт результатов

```python
from mysql_connector import get_keyword_count, get_genre_year_count

# Подсчёт для поиска по ключевому слову
count = get_keyword_count("matrix", genre_id=1, year_min=2005, year_max=2010)
print(f"Найдено: {count} фильмов")

# Подсчёт для поиска по жанру
count = get_genre_year_count(genre_id=1, year_min=2005, year_max=2010)
print(f"Найдено: {count} фильмов")
```

### Получение актёров фильма

```python
from mysql_connector import get_actors_by_film

actors = get_actors_by_film(film_id=1)
for actor in actors:
    print(f"{actor['first_name']} {actor['last_name']}")
```

### Получение фильмов актёра

```python
from mysql_connector import get_films_by_actor, get_films_by_actor_count

# Подсчёт фильмов актёра
count = get_films_by_actor_count(actor_id=1)
print(f"Актёр снялся в {count} фильмах")

# Получение списка фильмов с пагинацией
films = get_films_by_actor(actor_id=1, offset=0, limit=10)
for film in films:
    print(f"{film['title']} ({film['release_year']})")

# Следующая страница
more_films = get_films_by_actor(actor_id=1, offset=10, limit=10)
```

### Получение списка рейтингов

```python
from mysql_connector import get_ratings

ratings = get_ratings()
print("Доступные рейтинги:", ratings)
```

## 📝 log_writer.py

### Логирование поискового запроса

```python
from log_writer import log_search

# Логирование поиска по ключевому слову
log_search(
    search_type="keyword",
    params={"keyword": "matrix", "genre_id": 1},
    results_count=5
)

# Логирование поиска по жанру
log_search(
    search_type="genre_year",
    params={"genre_id": 1, "year_min": 2005, "year_max": 2010},
    results_count=15
)
```

## 📊 log_stats.py

### Получение популярных запросов

```python
from log_stats import get_top_queries

top_queries = get_top_queries(limit=5)
for query in top_queries:
    print(f"Запрос: {query['_id']}")
    print(f"Количество: {query['count']}")
    print(f"Последний: {query['last']}")
```

### Получение недавних запросов

```python
from log_stats import get_last_queries

recent_queries = get_last_queries(limit=5)
for query in recent_queries:
    print(f"[{query['timestamp']}] {query['search_type']}")
    print(f"Параметры: {query['params']}")
    print(f"Результатов: {query['results_count']}")
```

### Очистка логов

```python
from log_stats import clear_logs

deleted_count = clear_logs()
print(f"Удалено записей: {deleted_count}")
```

## 🎨 formatter.py

### Вывод списка фильмов

```python
from formatter import print_movies_table

films = [
    {
        "title": "Matrix",
        "release_year": 2006,
        "rental_rate": 2.99,
        "replacement_cost": 19.99,
        "rating": "PG-13",
        "description": "A computer hacker learns..."
    }
]

# Простой вывод
print_movies_table(films)

# С информацией о пагинации
print_movies_table(films, offset=0, total=100, show_header=True)
```

### Вывод списка жанров

```python
from formatter import print_genres

genres = [
    {"category_id": 1, "name": "Action"},
    {"category_id": 2, "name": "Animation"}
]

print_genres(genres)
```

### Вывод статистики

```python
from formatter import print_stats

top_queries = [...]  # из get_top_queries()
last_queries = [...]  # из get_last_queries()

print_stats(top_queries, last_queries)
```

### Вывод актёров

```python
from formatter import print_actors

actors = [
    {"first_name": "John", "last_name": "Doe"},
    {"first_name": "Jane", "last_name": "Smith"}
]

print_actors(actors, film_title="Matrix")
```

## ⚙️ config.py

### Использование конфигурации

```python
from config import (
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_DB,
    LIMIT,
    RATING_ORDER,
    RATING_DESCRIPTIONS
)

print(f"Подключение к: {MYSQL_HOST}")
print(f"База данных: {MYSQL_DB}")
print(f"Результатов на странице: {LIMIT}")
print(f"Порядок рейтингов: {RATING_ORDER}")

# Получение описания рейтинга
rating = "PG-13"
description = RATING_DESCRIPTIONS.get(rating, "Неизвестный рейтинг")
print(f"{rating}: {description}")
```

## 🔄 Комплексный пример

```python
from mysql_connector import search_by_keyword, get_actors_by_film, get_films_by_actor
from log_writer import log_search
from formatter import print_movies_table, print_actors

# 1. Поиск фильмов
keyword = "love"
films = search_by_keyword(keyword, offset=0, limit=10)

# 2. Вывод результатов
print_movies_table(films, offset=0, total=len(films))

# 3. Логирование
log_search("keyword", {"keyword": keyword}, len(films))

# 4. Получение актёров первого фильма
if films:
    film = films[0]
    actors = get_actors_by_film(film['film_id'])
    print_actors(actors, film_title=film['title'])
    
    # 5. Получение фильмов первого актёра
    if actors:
        actor = actors[0]
        actor_films = get_films_by_actor(actor['actor_id'], offset=0, limit=10)
        actor_name = f"{actor['first_name']} {actor['last_name']}"
        print(f"\nФильмы актёра {actor_name}:")
        print_movies_table(actor_films)
```

## 🔐 Безопасность

### Правильное использование подключений

```python
from mysql_connector import get_connection

# ПРАВИЛЬНО: использование context manager
with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM film LIMIT 10")
        results = cursor.fetchall()

# НЕПРАВИЛЬНО: забыли закрыть соединение
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM film")
# Утечка соединения!
```

### Обработка ошибок

```python
from mysql_connector import search_by_keyword

try:
    films = search_by_keyword("matrix")
    if not films:
        print("Фильмы не найдены")
except RuntimeError as e:
    print(f"Ошибка подключения к БД: {e}")
except Exception as e:
    print(f"Неожиданная ошибка: {e}")
```

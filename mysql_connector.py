"""Подключение к MySQL и выполнения запросов.
Все функции возвращают списки словарей (DictCursor) для удобства.
"""

import pymysql
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DB, LIMIT, RATING_ORDER


def get_ratings_lesser_or_equal(rating):
    """Возвращает список рейтингов, включающий `rating` и более мягкие.
    Например, если rating="PG-13", вернёт ["G","PG","PG-13"].
    Если рейтинг не найден — вернёт список из самого значения.
    """
    if not rating:
        return []
    try:
        idx = RATING_ORDER.index(rating)
    except ValueError:
        return [rating]
    # вернуть все рейтинги до и включая выбранный
    return RATING_ORDER[: idx + 1]


def get_connection():
    """Возвращает новое подключение PyMySQL с использованием DictCursor.
    Используйте `with` для корректного закрытия.
    """
    try:
        return pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    except pymysql.err.OperationalError as exc:
        msg = (
            f"Не удалось подключиться к MySQL ({exc}).\n"
            "Проверьте наличие сервера MySQL или правильность параметров в .env"
        )
        raise RuntimeError(msg) from exc


def get_genres():
    """Возвращает список жанров (category_id, name)."""

    query = "SELECT category_id, name FROM category ORDER BY name"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def get_ratings():
    """Возвращает список доступных значений `rating` из таблицы `film`."""

    query = "SELECT DISTINCT rating FROM film WHERE rating IS NOT NULL"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            db_ratings = [r.get("rating") for r in rows]

            ordered = [r for r in RATING_ORDER if r in db_ratings]
            others = [r for r in db_ratings if r not in ordered]
            return ordered + others


def get_year_bounds():
    """Возвращает кортеж `(min_year, max_year)` по данным таблицы `film`."""
    query = "SELECT MIN(release_year) AS min_year, MAX(release_year) AS max_year FROM film"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            return row.get("min_year"), row.get("max_year")


def search_by_keyword(
        keyword,
        offset=0,
        limit=LIMIT,
        genre_id=None,
        year_min=None,
        year_max=None,
        rating=None):
    """Поиск фильмов по ключевому слову с опциональными фильтрами.
    Поддерживаются фильтры: `genre_id`, `year_min`/`year_max`, `rating`.
    """
    params = []
    where_clauses = ["f.title LIKE %s"]
    params.append(f"%{keyword}%")

    join_clause = ""
    if genre_id is not None:
        join_clause = "JOIN film_category fc ON f.film_id = fc.film_id"
        where_clauses.append("fc.category_id = %s")
        params.append(int(genre_id))

    if year_min is not None and year_max is not None:
        where_clauses.append("f.release_year BETWEEN %s AND %s")
        params.append(int(year_min))
        params.append(int(year_max))

    if rating:
        allowed = get_ratings_lesser_or_equal(rating)
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            where_clauses.append(f"f.rating IN ({placeholders})")
            params.extend(allowed)

    where_sql = " AND ".join(where_clauses)
    query = (
        "SELECT DISTINCT f.film_id, f.title, f.description, "
        "f.release_year, f.rating, f.rental_rate, "
        "f.replacement_cost "
        "FROM film f "
        f"{join_clause} "
        f"WHERE {where_sql} "
        "ORDER BY f.title "
        "LIMIT %s OFFSET %s"
    )
    params.extend([int(limit), int(offset)])
    query = query.format(join_clause=join_clause, where_sql=where_sql)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()


def search_by_genre_and_year(
        genre_id,
        year_min,
        year_max,
        offset=0,
        limit=LIMIT,
        rating=None):
    """Поиск фильмов по жанру и диапазону лет с опциональным фильтром `rating`."""
    params = [int(genre_id), int(year_min), int(year_max)]
    query = (
        "SELECT DISTINCT f.film_id, f.title, f.description, "
        "f.release_year, f.rating, f.rental_rate, "
        "f.replacement_cost "
        "FROM film f "
        "JOIN film_category fc ON f.film_id = fc.film_id "
        "WHERE fc.category_id = %s "
        "AND f.release_year BETWEEN %s AND %s ")
    if rating:
        allowed = get_ratings_lesser_or_equal(rating)
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            query += f"AND f.rating IN ({placeholders}) "
            params = [int(genre_id), int(year_min), int(year_max)] + allowed
        else:
            params = [int(genre_id), int(year_min), int(year_max)]
    query += "ORDER BY f.title LIMIT %s OFFSET %s"
    params.extend([int(limit), int(offset)])
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()


def get_keyword_count(
        keyword,
        genre_id=None,
        year_min=None,
        year_max=None,
        rating=None):
    """Возвращает общее число фильмов, соответствующих ключу и фильтрам."""
    params = []
    where_clauses = ["f.title LIKE %s"]
    params.append(f"%{keyword}%")
    join_clause = ""
    if genre_id is not None:
        join_clause = "JOIN film_category fc ON f.film_id = fc.film_id"
        where_clauses.append("fc.category_id = %s")
        params.append(int(genre_id))
    if year_min is not None and year_max is not None:
        where_clauses.append("f.release_year BETWEEN %s AND %s")
        params.append(int(year_min))
        params.append(int(year_max))
    if rating:
        allowed = get_ratings_lesser_or_equal(rating)
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            where_clauses.append(f"f.rating IN ({placeholders})")
            params.extend(allowed)
    where_sql = " AND ".join(where_clauses)
    query = f"SELECT COUNT(DISTINCT f.film_id) AS cnt FROM film f {join_clause} WHERE {where_sql}"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return int(row.get("cnt", 0))


def get_genre_year_count(genre_id, year_min, year_max, rating=None):
    """Вернуть количество фильмов для жанра/диапазона лет и опц. рейтинга."""
    params = [int(genre_id), int(year_min), int(year_max)]
    query = (
        "SELECT COUNT(DISTINCT f.film_id) AS cnt "
        "FROM film f "
        "JOIN film_category fc ON f.film_id = fc.film_id "
        "WHERE fc.category_id = %s AND f.release_year BETWEEN %s AND %s"
    )
    if rating:
        allowed = get_ratings_lesser_or_equal(rating)
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            query += f" AND f.rating IN ({placeholders})"
            params.extend(allowed)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return int(row.get("cnt", 0))


def get_actors_by_film(film_id):
    """Возвращает список актёров (actor_id, first_name, last_name) для фильма по `film_id`.

    Результат — список словарей, упорядоченных по фамилии, затем по имени.
    """
    query = (
        "SELECT a.actor_id, a.first_name, a.last_name "
        "FROM actor a "
        "JOIN film_actor fa ON a.actor_id = fa.actor_id "
        "WHERE fa.film_id = %s "
        "ORDER BY a.last_name, a.first_name"
    )
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (int(film_id),))
            return cursor.fetchall()


def get_films_by_actor(actor_id, offset=0, limit=LIMIT):
    """Возвращает список фильмов с участием актёра по `actor_id`.

    Результат — список словарей с информацией о фильмах,
    упорядоченных по названию фильма.
    """
    query = (
        "SELECT DISTINCT f.film_id, f.title, f.description, f.release_year, "
        "f.rating, f.rental_rate, f.replacement_cost "
        "FROM film f "
        "JOIN film_actor fa ON f.film_id = fa.film_id "
        "WHERE fa.actor_id = %s "
        "ORDER BY f.title "
        "LIMIT %s OFFSET %s"
    )
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (int(actor_id), int(limit), int(offset)))
            return cursor.fetchall()


def get_films_by_actor_count(actor_id):
    """Возвращает количество фильмов с участием актёра."""
    query = (
        "SELECT COUNT(DISTINCT f.film_id) AS cnt "
        "FROM film f "
        "JOIN film_actor fa ON f.film_id = fa.film_id "
        "WHERE fa.actor_id = %s"
    )
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (int(actor_id),))
            row = cursor.fetchone()
            return int(row.get("cnt", 0))

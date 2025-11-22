"""Хелперы форматирования для консольного вывода.

Здесь собраны функции вывода результатов поиска, списков жанров,
диапазонов лет и статистики. Функции ориентированы на удобное чтение в
терминале; при необходимости их можно заменить на более богатую табличную
печать (например, с помощью `tabulate`).
"""


# Визуальный разделитель, печатаемый после блока результатов
SEPARATOR = "*" * 100


def _truncate(text, length=120):
    """Усечь `text` до `length` символов, добавив '...' при необходимости."""
    if text is None:
        return ""
    text = str(text)
    return text if len(text) <= length else text[: length - 3] + "..."


def _fmt_money(x):
    """Format numeric money-like value to two decimals or return 'N/A'."""
    if x is None:
        return "N/A"
    try:
        return f"{float(x):.2f}"
    except Exception:
        return str(x)





def print_movies_table(films, offset=0, total=None, show_header=True):
    """Вывести список фильмов с нумерацией начиная от `offset + 1`.

    Если передан `total`, в шапке отображается диапазон и общее число,
    например: "Показаны 1–10 из 42".
    Каждый фильм выводится в формате: `1. Название (Год)` и краткое
    описание на следующей строке (усечённое через `_truncate`).
    """
    if not films:
        print("Фильмы не найдены")
        return
    # Заголовок с информацией о диапазоне и общим количеством
    if show_header:
        if total is not None:
            start = offset + 1
            end = offset + len(films)
            print(f"=== Результаты (Показаны {start}–{end} из {total}) ===")
        else:
            print("=== Результаты ===")

    for i, film in enumerate(films, start=offset + 1):
        title = film.get("title")
        year = film.get("release_year")
        rental = film.get("rental_rate")
        replacement = film.get("replacement_cost")
        desc_raw = film.get("description")
        desc = _truncate(desc_raw, 120)
        rental_s = _fmt_money(rental)
        replacement_s = _fmt_money(replacement)
        print(f"{i}. {title} ({year}) — аренда: {rental_s}, покупка: {replacement_s}")
        if desc:
            print(f"    {desc}")
    # Разделитель печатается вызывающей стороной после вывода страницы


def print_genres(genres):
    """Вывести список жанров с индексами для выбора пользователем.

    Ожидаемый формат: `1. НазваниеЖанра (id: category_id)`.
    """
    if not genres:
        print("Жанры не найдены в базе.")
        return
    print("=== Жанры ===")
    for idx, g in enumerate(genres, start=1):
        print(f"{idx}. {g.get('name')} (id: {g.get('category_id')})")


def print_year_bounds(min_year, max_year):
    """Показать минимальный и максимальный годы релизов, найденные в БД."""
    print(f"Доступные годы: {min_year} — {max_year}")


def print_stats(top_queries, last_queries):
    """Вывести статистику популярных и последних запросов из MongoDB.

    `top_queries` ожидается как список агрегированных документов, где
    `_id` содержит `type` и `params` (мы группируем по `user_params`).
    """
    print("=== Популярные запросы ===")
    if not top_queries:
        print("Статистика недоступна.")
    for item in top_queries:
        _id = item.get("_id")
        count = item.get("count")
        last = item.get("last")
        # Печатаем тип запроса и параметры в читабельном виде
        print(f"- тип={_id.get('type')}, параметры={_id.get('params')} -> кол-во={count}, последний={last}")

    print("=== Недавние запросы ===")
    if not last_queries:
        print("Недавних запросов нет.")
    for q in last_queries:
        print(f"- {q.get('timestamp')}: {q.get('search_type')} {q.get('params')} -> {q.get('results_count')}")


def print_actors(actors, film_title=None):
    """Печать списка актёров для выбранного фильма.

    `actors` — список словарей с ключами `actor_id`, `first_name`, `last_name`.
    """
    if film_title:
        print(f"\nАктёры фильма: {film_title}\n")
    if not actors:
        print("Актёры не найдены.")
        return
    for a in actors:
        # Печатаем имена в верхнем регистре для единообразного отображения
        fn = (a.get('first_name') or '').strip().upper()
        ln = (a.get('last_name') or '').strip().upper()
        print(f"- {fn} {ln}")
    print(f"\nВсего актёров: {len(actors)}")

